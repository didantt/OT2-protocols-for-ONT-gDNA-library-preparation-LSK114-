from opentrons import protocol_api, types


metadata = {
    "apiLevel": "2.16",
    "protocolName": "NB3: Adapter Ligation",
    "description": """Third part of the SQK-NBD114.24 Nanopore protocol. Uses same reagents. Protocol assumes kit tubes are used.""",
    "author": "Didrik Anttila"
    }

""" Material requirements

PBs: Pooled Barcoded Sample 
NA: Native Adapter
QL: Quickl ligation T4 Ligase
QB: Quick Ligation buffer
LFB: Long Fragment Buffer
EB: Elution Buffer
AXP: AXP beads
H2O: de-ionized milliQ water
Eth: 96% Ethanol
QB: Invitrogen 1X dsDNA BR Working Solution

Positioning in labware

Ep tuberack
A1: AXP
A2: Empty 1.5mL eppendorf

Temperature module
A1: PBs ((30µL))
A2: NA ((5µL))
B1: LFB ((300µL))
B2: EB ((15µL))
C1: QL ((5µL))
C2: QB ((10µL))

Falcon tube rack
A1: QB ((3-4mL?))
A3: H2O ((? nearly full))
B3: 80% Eth ((Near empty or empty))
B4: 96% Eth ((Near full))
"""


num_samples = 2
if num_samples not in range(1, 24):
    raise Exception("Number of samples not between 1 and 24.")




def run(protocol: protocol_api.ProtocolContext):
    # Labware
    big_tips = protocol.load_labware("opentrons_96_tiprack_300ul", 8) 
    small_tips = protocol.load_labware("opentrons_96_tiprack_20ul", 4)
    reservoir = protocol.load_labware("nest_1_reservoir_290ml", 5) # Actually pipette tip box lid
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", 2) 
    ep_tuberack = protocol.load_labware("opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap", 10)
    falcon_tuberack = protocol.load_labware("opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical", 6)
    
    # Hardware modules
    hs_mod = protocol.load_module(
        module_name="heaterShakerModuleV1", 
        location="1")
    hs_adapter = hs_mod.load_adapter(
        "opentrons_96_pcr_adapter") # ? I think this is the adapter we will use.
    hs_plate = hs_adapter.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt") # ? 
    

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



    # Procedure / commands
    hs_mod.close_labware_latch()

    protocol.comment("* Adding SUSPENDED beads to hs plate.")
    left_pipette.pick_up_tip()
    left_pipette.mix(5, 100, ep_tuberack["A1"])
    left_pipette.blow_out()
    left_pipette.aspirate(35, ep_tuberack["A1"])
    left_pipette.touch_tip(radius=0.85, speed=5)
    left_pipette.touch_tip(radius=0.85, speed=5)
    left_pipette.air_gap(volume=5)
    left_pipette.dispense(40, hs_plate["H3"])
    left_pipette.blow_out()
    left_pipette.drop_tip()
    
    temp_mod.set_temperature(celsius=4)

    protocol.comment("* Adding and mixing barcoded sample with quick ligation reagents. Mixing before use.")
    
    # Barcoded sample
    #left_pipette.transfer(30, temp_labware["A1"], mag_plate["G1"], mix_before=(10, 30), blow_out=True, blowout_location="destination well") # Barcoded sample
    left_pipette.pick_up_tip()
    left_pipette.mix(10, 28, temp_labware["A1"])
    left_pipette.aspirate(30, temp_labware["A1"], rate=0.5)
    left_pipette.default_speed = 100
    left_pipette.dispense(30, mag_plate["G1"].top(z=-2))
    left_pipette.blow_out()
    left_pipette.default_speed = 400
    left_pipette.drop_tip()

    # Native adapter
    #right_pipette.transfer(5, temp_labware["A2"], mag_plate["G1"].bottom(z=-1.5), mix_before=(10, 5), blow_out=True, blowout_location="destination well") # Native adapter
    right_pipette.pick_up_tip()
    right_pipette.mix(10, 5, temp_labware["A2"])
    right_pipette.aspirate(5, temp_labware["A2"], rate=0.5)
    right_pipette.default_speed = 50
    right_pipette.dispense(5, mag_plate["G1"])
    right_pipette.blow_out()
    right_pipette.touch_tip(mag_plate["G1"], radius=0.6, v_offset=-2, speed=2)
    right_pipette.default_speed = 400
    right_pipette.drop_tip()

    # Ligation buffer
    right_pipette.transfer(10, temp_labware["C2"], mag_plate["G1"], mix_before=(10, 10), blow_out=True, blowout_location="destination well") # Ligation buffer
    right_pipette.pick_up_tip()
    right_pipette.mix(10, 20, temp_labware["C2"])
    right_pipette.air_gap(volume=5) # why is this before aspiration?
    right_pipette.aspirate(10, temp_labware["C2"], rate=0.5)
    right_pipette.touch_tip(temp_labware["C2"], radius=0.55, speed=5)
    right_pipette.default_speed = 100
    right_pipette.dispense(15, mag_plate["G1"].top(z=-1))
    right_pipette.blow_out()
    right_pipette.touch_tip(mag_plate["G1"], radius=0.75, v_offset=-2, speed=2)
    right_pipette.default_speed = 400
    right_pipette.drop_tip()
    
    # T4 Ligase
    right_pipette.pick_up_tip()
    right_pipette.mix(10, 20, temp_labware["C1"])
    right_pipette.blow_out()
    right_pipette.aspirate(5, temp_labware["C1"], rate=0.2)
    right_pipette.default_speed = 50
    right_pipette.touch_tip(temp_labware["C1"], radius=0.55, speed=5)
    right_pipette.dispense(5, mag_plate["G1"])
    right_pipette.blow_out()
    right_pipette.touch_tip(mag_plate["G1"], radius=0.85, v_offset=-1, speed=2)
    right_pipette.default_speed = 400
    right_pipette.drop_tip()
    ###

    # Mixing solution
    left_pipette.pick_up_tip()
    left_pipette.mix(5, 25, mag_plate["G1"], rate=0.5)
    left_pipette.blow_out()
    left_pipette.touch_tip(mag_plate["G1"], radius=0.85, speed=1)
    left_pipette.drop_tip()

    protocol.comment("* Incubating for 20 min at RT.")
    protocol.delay(minutes=20)

    protocol.comment("* Suspending beads and adding 20uL to sample. Suspending.")
    hs_mod.set_and_wait_for_shake_speed(900)
    protocol.delay(2)
    hs_mod.deactivate_shaker()

    left_pipette.pick_up_tip()
    left_pipette.mix(10, 20, hs_plate["H3"])
    left_pipette.blow_out(hs_plate["H3"])
    left_pipette.aspirate(20, hs_plate["H3"])
    left_pipette.touch_tip(hs_plate["H3"], radius=0.85, speed=2)
    left_pipette.touch_tip(hs_plate["H3"], radius=0.85, speed=2)
    left_pipette.dispense(20, mag_plate["G1"].top(z=0))
    left_pipette.mix(8, 60, mag_plate["G1"])

    protocol.comment("* Hula mixing for 10 minutes.")
    left_pipette.mix(117, 35, mag_plate["G1"], rate=0.25) # 117 needs to be doubled from barcode ligation, since nearly half the sample.

    left_pipette.blow_out(mag_plate["G1"])
    left_pipette.touch_tip(mag_plate["G1"], radius=0.85, speed=2)
    left_pipette.drop_tip()

    protocol.comment("* Pelleting beads on magnet.")
    mag_mod.engage(height_from_base=8.5)
    protocol.delay(minutes=5)

    protocol.comment("* Dumping supernatant")
    left_pipette.pick_up_tip()
    right_pipette.pick_up_tip()
    left_pipette.aspirate(70, mag_plate["G1"], rate=0.02)
    left_pipette.dispense(70, reservoir["A1"].bottom(z=30))
    left_pipette.drop_tip()
    right_pipette.aspirate(20, mag_plate["G1"], rate=0.1)
    right_pipette.drop_tip()

    hs_mod.set_target_temperature(37) # Setting target temp in advance

    protocol.comment("* Washing beads with Long Fragment Buffer twice, dumping the supernatant.")
    mag_mod.disengage()
    for i in range(2): # Repeat once
        left_pipette.pick_up_tip()
        right_pipette.pick_up_tip()
        left_pipette.mix(10, 300, temp_labware["B1"])
        left_pipette.aspirate(125, temp_labware["B1"]) # Height offset?
        left_pipette.touch_tip(temp_labware["B1"], radius=0.55, speed=5)
        left_pipette.dispense(125, mag_plate["G1"])
        left_pipette.mix(5, 120, mag_plate["G1"])
        left_pipette.blow_out(mag_plate["G1"])
        left_pipette.drop_tip()
        # 8.5 extension first time, then lower to 4.5
        if i == 0:
            protocol.comment("* Engaging magnet with height 8.5")
            mag_mod.engage(height_from_base=(8.5))
        elif i == 1:
            protocol.comment("* Engaging magnet with height 4.5")
            mag_mod.engage(height_from_base=(4.5))
        protocol.delay(minutes=5)
        left_pipette.pick_up_tip()
        left_pipette.aspirate(150, mag_plate["G1"], rate=0.02)
        left_pipette.air_gap(volume=30)
        left_pipette.dispense(180, reservoir["A1"].bottom(z=30))
        left_pipette.blow_out()
        left_pipette.drop_tip()
        protocol.delay(seconds=30) # Because no spin down, allow fluid to slowly collect.
        right_pipette.aspirate(10, mag_plate["G1"], rate=0.1)
        right_pipette.drop_tip()

        mag_mod.disengage()

    protocol.comment("* Suspending pellet in Elution Buffer, and moving to hs plate.")
    # ! Perhaps in this step, one could simply use only the large pipette by having it aspirate a 5µL air gap before aspirating the 15µL Elution Buffer?
    right_pipette.pick_up_tip()
    right_pipette.mix(10, 14, temp_labware["B2"])
    right_pipette.aspirate(7, temp_labware["B2"])
    right_pipette.default_speed = 100
    right_pipette.dispense(7, mag_plate["G1"])
    right_pipette.blow_out(mag_plate["G1"])
    right_pipette.touch_tip(mag_plate["G1"])
    right_pipette.default_speed = 400
    right_pipette.mix(5, 6, mag_plate["G1"])
    right_pipette.aspirate(15, mag_plate["G1"], rate=0.5) # Aspirate slowly to attempt to get as much solution as possible.
    right_pipette.air_gap(volume = 5)
    right_pipette.dispense(20, hs_plate["E1"])
    right_pipette.blow_out()
    right_pipette.touch_tip(hs_plate["E1"], radius=0.85, speed=2)
    right_pipette.drop_tip()

    hs_mod.wait_for_temperature()
    protocol.comment("* Incubating for 10 minutes, agitating sample each second minute for 10 seconds.")
    protocol.delay(minutes=2)
    for i in range(4): # Repeating this step 4 times
        hs_mod.set_and_wait_for_shake_speed(500) 
        protocol.delay(seconds=10)
        hs_mod.deactivate_shaker()
        protocol.delay(seconds=110)
    # Total time 10 minutes. (ignoring spinup time)
    hs_mod.deactivate_heater()

    protocol.comment("* Suspending solution and pelleting on magnet for 5 minutes.")
    right_pipette.pick_up_tip()
    right_pipette.mix(10, 10, hs_plate["E1"])
    protocol.pause("Suspended enough? (hs well E1)")
    right_pipette.aspirate(15, hs_plate["E1"], rate=0.5)
    right_pipette.dispense(15, mag_plate["H1"])
    right_pipette.blow_out(mag_plate["H1"])
    right_pipette.touch_tip(radius=0.85, speed=1)
    right_pipette.drop_tip()

    mag_mod.engage(height_from_base=8.5)
    # Protocol recommends 1 minute. 
    # Experience recommends 2 minutes. 
    # Apply 5 minutes, because beads will not have been spun down and be fully suspended when put on magnet.
    protocol.delay(minutes=5) 



    left_pipette.pick_up_tip()
    left_pipette.aspirate(199, falcon_tuberack["A1"].bottom(z=3))
    left_pipette.dispense(199, plate["E1"])


    protocol.comment("* Extracting supernatant and placing in empty eppendorf in temp module slot D1")
    right_pipette.pick_up_tip()
    right_pipette.aspirate(10, mag_plate["H1"], rate=0.1)
    right_pipette.dispense(10, ep_tuberack["A2"])
    right_pipette.blow_out()
    right_pipette.touch_tip(ep_tuberack["A2"], radius=0.85, speed=3)

    right_pipette.aspirate(1, ep_tuberack["A2"])
    right_pipette.dispense(1, plate["E1"])
    left_pipette.mix(5, 100, plate["E1"])

    right_pipette.drop_tip()
    left_pipette.drop_tip()


    hs_mod.open_labware_latch()