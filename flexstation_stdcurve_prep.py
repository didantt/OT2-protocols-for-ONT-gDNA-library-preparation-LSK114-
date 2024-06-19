from opentrons import protocol_api, types


metadata = {
    "apiLevel": "2.16",
    "protocolName": "Flexstation Standard curve",
    "description": """Makes a serial dilution on a plate for calibration of Flexstation, and adds DNA samples for test reading.""",
    "author": "Didrik Anttila"
    }

"""
Prerequisites

Eppendorf tuberack: 
A1 = DNA sample, min ~1µL (optional)
A2 = 100ng/µL calibration fluid, min 30µL : Invitrogen Qubit dsDNA BR Standard #2 100ng/µL
A3 = 0ng/µL calibration fluid, min 30µL : Invitrogen Qubit dsDNA BR Standard #1 0ng/µL
A4 = Qubit solution, min ~1350µL (1.35mL) : Invitrogen 1X dsDNA BR Working Solution
"""


def run(protocol: protocol_api.ProtocolContext):
    # Labware
    big_tips = protocol.load_labware("opentrons_96_tiprack_300ul", 8) 
    small_tips = protocol.load_labware("opentrons_96_tiprack_20ul", 4)
    reservoir = protocol.load_labware("nest_1_reservoir_290ml", 5) 
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", 2) 
    ep_tuberack = protocol.load_labware("opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap", 10)
    falcon_tuberack = protocol.load_labware("opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical", 6)
    
    # Hardware modules
    hs_mod = protocol.load_module(
        module_name="heaterShakerModuleV1", 
        location="1")
    hs_adapter = hs_mod.load_adapter(
        "opentrons_96_pcr_adapter") 
    hs_plate = hs_adapter.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt") 

    mag_mod = protocol.load_module(
        module_name = "magnetic module gen2", 
        location="9")
    mag_plate = mag_mod.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt") 
    
    temp_mod = protocol.load_module(
        module_name = "temperature module gen2",
        location = "3")
    temp_labware = temp_mod.load_labware("opentrons_24_aluminumblock_nest_1.5ml_snapcap")

    # Pipette
    # The p300 pipette is generally best suited for volumes in the range 30-300µL. 
    # The P20 pipette is best suited for volumes in the range 1-20µL.
    left_pipette = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[big_tips]) 
    right_pipette = protocol.load_instrument("p20_single_gen2", "right", tip_racks=[small_tips])


    # Procedure
    hs_mod.close_labware_latch()

    left_pipette.pick_up_tip()
    left_pipette.transfer(190, ep_tuberack["A4"], [plate["A3"], plate["B3"], plate["C3"], plate["D3"], plate["E3"], plate["F3"]], new_tip="never", touch_tip=True)
    left_pipette.drop_tip()


    # Broad range calibration fluid 100ng/µL
    right_pipette.pick_up_tip()
    right_pipette.transfer(10, ep_tuberack["A2"], plate["A3"], new_tip="never", touch_tip=True)
    right_pipette.transfer(8, ep_tuberack["A2"], plate["B3"], new_tip="never", touch_tip=True)
    right_pipette.transfer(6, ep_tuberack["A2"], plate["C3"], new_tip="never", touch_tip=True)
    right_pipette.transfer(4, ep_tuberack["A2"], plate["D3"], new_tip="never", touch_tip=True)
    right_pipette.transfer(2, ep_tuberack["A2"], plate["E3"], new_tip="never", touch_tip=True)
    right_pipette.drop_tip()
    

    # Broad range calibration fluid 0ng/µL # Touch tip was a bit fast, and did not dislodge the droplet which was higher up.
    right_pipette.transfer(2, ep_tuberack["A3"], plate["B3"], mix_after=(10, 20), touch_tip=True)
    right_pipette.transfer(4, ep_tuberack["A3"], plate["C3"], mix_after=(10, 20), touch_tip=True)
    right_pipette.transfer(6, ep_tuberack["A3"], plate["D3"], mix_after=(10, 20), touch_tip=True)
    right_pipette.transfer(8, ep_tuberack["A3"], plate["E3"], mix_after=(10, 20), touch_tip=True)
    right_pipette.transfer(10, ep_tuberack["A3"], plate["F3"], mix_after=(10, 20), touch_tip=True)

    # DNA sample
    # right_pipette.transfer(1, ep_tuberack["A1"], plate["H3"], mix_after=(10, 20))


    protocol.pause("Bring plate to Flexstation, also bring qubit solution and DNA sample for Qubit control test.")