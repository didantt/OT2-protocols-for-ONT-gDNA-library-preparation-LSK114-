from opentrons import protocol_api
import io

metadata = {
    "apiLevel": "2.16",
    "protocolName": "NBD2: Barcode ligation",
    "description": """Second part of the SQK-NBD114.24 Nanopore protocol. Uses same reagents. Protocol assumes kit tubes are used.""",
    "author": "Didrik Anttila"
    }



""" Material requirements

EpS: End-prepped DNA (Max 7.5uL/sample)
BLT: Blunt/TA Ligase Master mix (10uL per sample)
BC: Unique Native Barcodes (2.5 per sample)
EDTA: EDTA (2 per sample)
AXP: AXP beads (0.4x of pooled volumes after EDTA addition)
H2O: de-ionized milliQ water
Eth: 96% Ethanol
QB: Invitrogen 1X dsDNA BR Working Solution

Positioning in labware

Ep tuberack
A1: AXP
A2: Empty 1.5mL eppendorf

Temperature module
A1: EpS1 ((10uL))
A2: EpS2 ((10uL))
B1: BC-01 ((3uL))
B2: BC-02 ((3uL))
C1: BLT ((11 uL))
C2: EDTA ((3 uL))
D1: Empty 1.5mL Ep tube

Falcon tube rack
A1: QB ((3-4mL?))
A3: H2O ((? nearly full))
B3: 80% Eth ((Near empty or empty))
B4: 96% Eth ((Near full))
"""

# Leave these at 0 if you want script to get the data on its own from jupyter notebook. I wouldn't recommend it without alterations to the data retrieval code however.
# FSC454
sample1_conc = 67.8 # ng/µL

# FSC454
sample2_conc = 36.6 # ng/µL




num_samples = 2
if num_samples not in range(1, 24):
    raise Exception("Number of samples not between 1 and 24.")


def run(protocol: protocol_api.ProtocolContext):
    # Labware
    big_tips = protocol.load_labware("opentrons_96_tiprack_300ul", 8) 
    small_tips = protocol.load_labware("opentrons_96_tiprack_20ul", 4)
    reservoir = protocol.load_labware("nest_1_reservoir_290ml", 5) 
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", 2) # Flexstation plate # eller nunc 96 flat bottom fast de verkar lika
    ep_tuberack = protocol.load_labware("opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap", 10)
    falcon_tuberack = protocol.load_labware("opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical", 6)
    # hs_plate = protocol.load_labware("nest_96_wellplate_200ul_flat", 1) # Pretend this is heater shaker
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

    # Sample with lowest concentration kept to volume 7.5uL
    # Other sample calculated to lower volume with same molar concentration. Water added to make 7.5uL later
    sample1_vol = 7.5 * (sample2_conc/sample1_conc) #µL
    sample2_vol = 7.5 #µL


    ### Block that reads file data. Must be in procedure and commands, and probably needs to be in a try-except.
    # Currently unused. Will assume the matrix comes from softmax pro in .txt format. Also that the calculated sample concentrations are the first two cells in column 1.
    # In practice these will be wherever the 'Unknown' cells have been designated in softmax pro. 
    # ! While it won't take much to get this method to work the way you want, I still do not fully recommend it because softmax pro will only be calculating the concentration based on
    # the standard dilution series you included on the same plate. It's better to create a standard curve function yourself from several replicates.
    ###########################################    

    tries = 0 


    while tries <= 3: # The user shouldn't need to specify which wells, if the robot already puts them in the same wells each time. Just the number of samples is enough.
        try:
            if sample1_conc == 0 or sample2_conc == 0: # This whole block of code only runs if the initial concentrations were set to 0
                sample_conc = io.open('DNArep_conc.txt','r', encoding='utf-16-le')
                conc_matrix = []
                for row in sample_conc.readlines()[2:]:
                    conc_matrix.append(row.strip().split('\t'))

                # for num in range(num_samples): # Make dynamic dictionary of samples later
                #     conc_matrix[num+1][1]

                #! Inflexible code, change after live run.
                # Acquires the concentrations of the first two samples.
                # Assigns the volume 7.5µL to the thinnest sample, and calculates what volume is needed of the thickest sample to have the same molar quantity.
                sample1_conc = float(conc_matrix[1][1])
                sample2_conc = float(conc_matrix[2][1])

            # ! Could be good to add a pause at the beginning of the protocol that lets the user check if the calculation seems reasonable.
            if sample1_conc > sample2_conc:
                sample2_vol = 7.5
                sample1_vol = sample2_vol*(sample2_conc/sample1_conc)

            elif sample2_conc > sample1_conc:
                sample1_vol = 7.5
                sample2_vol = sample1_vol*(sample1_conc/sample2_conc)

            tries = 4

        except:
            protocol.comment("* File not found.")
            tries += 1
    ###########################################    


    hs_mod.close_labware_latch()

    protocol.pause(f"The calculated sample volumes were Sample 1: {sample1_vol}, Sample 2: {sample2_vol}. Does this seem correct? If not, cancel protocol.")

    # Some of these reagents are too viscous to mix. (figure out which!)
    
    # Assumes beads in eppendorf tube in slot A1 were suspended immediately before starting the protocol.
    protocol.comment("* Adding SUSPENDED beads to heater shaker wells")

    left_pipette.pick_up_tip()
    left_pipette.mix(5, 100, ep_tuberack["A1"])
    left_pipette.blow_out()
    left_pipette.aspirate(50, ep_tuberack["A1"], rate=0.5) # Reactant tube
    left_pipette.default_speed = 100
    left_pipette.air_gap(volume=10)
    left_pipette.touch_tip(ep_tuberack["A1"], radius=0.6, speed=2)
    left_pipette.touch_tip(ep_tuberack["A1"], radius=0.6, speed=2)
    left_pipette.dispense(60, hs_plate["H2"])
    left_pipette.blow_out()
    left_pipette.drop_tip()
    left_pipette.default_speed = 400

    temp_mod.set_temperature(celsius=4) # The protocol will wait for the temperature to be reached before proceeding, omit this step while testing.
    protocol.comment(f"* Temperature module now 4C. The number of end-prepped samples is {num_samples}")


    protocol.comment("Adding samples to mag plate...")
    # The transfer of water should not initiate if the volume is 0
    right_pipette.transfer(sample1_vol, temp_labware["A1"], mag_plate["C1"], mix_before=(10, 10), blow_out=True, blowout_location="destination well")
    right_pipette.transfer(7.5-sample1_vol, falcon_tuberack["A3"].bottom(z=60), mag_plate["C1"])
    right_pipette.transfer(sample2_vol, temp_labware["A2"], mag_plate["C2"], mix_before=(10, 10), blow_out=True, blowout_location="destination well")
    right_pipette.transfer(7.5-sample2_vol, falcon_tuberack["A3"].bottom(z=60), mag_plate["C2"])

    protocol.comment("Adding barcodes to mag plate...")
    right_pipette.transfer(2.5, temp_labware["B1"].bottom(z=18), mag_plate["C1"], mix_before=(10, 15), blow_out=True, blowout_location="destination well") # flowrate?
    right_pipette.transfer(2.5, temp_labware["B2"].bottom(z=18), mag_plate["C2"], mix_before=(10, 15), blow_out=True, blowout_location="destination well")

    protocol.comment("Adding Blunt/TA Ligase Master Mix to mag plate...")
    
    left_pipette.pick_up_tip()
    left_pipette.mix(10, 300, temp_labware["C1"])
    left_pipette.blow_out()
    left_pipette.touch_tip(temp_labware["C1"], radius=0.55, speed=3)
    left_pipette.drop_tip()

    right_pipette.pick_up_tip()
    right_pipette.aspirate(10, temp_labware["C1"], rate=0.1)
    right_pipette.touch_tip(temp_labware["C1"], radius=0.55, speed=3)
    right_pipette.dispense(10, mag_plate["C1"])
    right_pipette.mix(10, 20, mag_plate["C1"])
    right_pipette.blow_out()
    right_pipette.drop_tip()

    right_pipette.pick_up_tip()
    right_pipette.aspirate(10, temp_labware["C1"], rate=0.1)
    right_pipette.touch_tip(temp_labware["C1"], radius=0.55, speed=3)
    right_pipette.dispense(10, mag_plate["C2"])
    right_pipette.mix(10, 20, mag_plate["C2"])
    right_pipette.blow_out()
    right_pipette.drop_tip()

    

    protocol.comment("* Incubating samples for 20 minutes.")
    protocol.delay(minutes=20)

    protocol.comment("* Mixing and adding EDTA to mag plates...")
    left_pipette.pick_up_tip()
    left_pipette.mix(10, 300, temp_labware["C2"])
    left_pipette.blow_out()
    left_pipette.drop_tip()

    # Sample 1
    right_pipette.pick_up_tip()
    right_pipette.aspirate(2, temp_labware["C2"])
    right_pipette.dispense(2, mag_plate["C1"])
    right_pipette.blow_out()
    right_pipette.drop_tip()

    left_pipette.pick_up_tip()
    left_pipette.mix(10, 20, mag_plate["C1"])
    left_pipette.blow_out()
    left_pipette.touch_tip(mag_plate["C1"], radius=0.85, speed=2)
    left_pipette.drop_tip()

    # Sample 2
    right_pipette.pick_up_tip()
    right_pipette.aspirate(2, temp_labware["C2"])
    right_pipette.dispense(2, mag_plate["C2"])
    right_pipette.blow_out()
    right_pipette.drop_tip()

    left_pipette.pick_up_tip()
    left_pipette.mix(10, 20, mag_plate["C2"])
    left_pipette.blow_out()
    left_pipette.touch_tip(mag_plate["C2"], radius=0.85, speed=2)
    left_pipette.drop_tip()
    

    protocol.comment("* Pooling samples into one well") # ! Only possible at fewer samples with smaller total volume! For many samples, pool in ep tube and then distribute in multiple wells.
    left_pipette.consolidate(30, [mag_plate["C1"], mag_plate["C2"]], mag_plate["E1"], mix_after=(5, 30), blow_out=True, blowout_location="destination well")


    protocol.comment("* Resuspending and adding 0.4X volume beads to pooled sample")
    hs_mod.set_and_wait_for_shake_speed(1000)
    protocol.delay(seconds=2)
    hs_mod.deactivate_shaker()

    left_pipette.pick_up_tip()
    right_pipette.pick_up_tip()
    left_pipette.mix(4, 30, hs_plate["H2"])
    left_pipette.blow_out()
    left_pipette.touch_tip(hs_plate["H2"], radius=0.85, v_offset=-2, speed=2) # Perhaps greater radius needed to touch
    left_pipette.touch_tip(hs_plate["H2"], radius=0.85, v_offset=-2, speed=2)
    right_pipette.aspirate(18, hs_plate["H2"], rate=0.5) # (22+22) * 0.4 = 17.6 ~= 18
    right_pipette.touch_tip(hs_plate["H2"], radius=0.85, v_offset=-2, speed=5) # Perhaps greater radius needed to touch
    right_pipette.touch_tip(hs_plate["H2"], radius=0.85, v_offset=-2, speed=5)
    right_pipette.dispense(18, mag_plate["E1"])
    right_pipette.blow_out()
    right_pipette.drop_tip()
    left_pipette.drop_tip()
    
    protocol.comment("* Pipette-mixing gently for 10 minutes. (In lieu of hula mixing)")
    
    left_pipette.pick_up_tip()
    left_pipette.mix(117, 60, mag_plate["E1"], rate=0.5) # Pipette flowrate at 92.86µL/s. Take that at half speed for both aspiration and dispension of 60µL, and multiply time to 5 minutes. 
    left_pipette.drop_tip()

    protocol.comment("* Engaging magnet")
    mag_mod.engage(height_from_base=7) # Perhaps 7mm instead of 8.5, since the beads are to be resuspended again.

    protocol.comment("* Preparing 2mL 80% Ethanol.")
    left_pipette.transfer(334, falcon_tuberack["A3"].bottom(z=60), falcon_tuberack["B3"].bottom(z=45))
    left_pipette.pick_up_tip()
    left_pipette.transfer(1667, falcon_tuberack["B4"].bottom(z=70), falcon_tuberack["B3"].bottom(z=45), new_tip = "never")
    left_pipette.mix(10, 300, falcon_tuberack["B3"])
    left_pipette.drop_tip()

    protocol.comment("* Allowing beads to pellet for 6 minutes.")
    protocol.delay(minutes=6)

    protocol.comment("* Extracting and dumping supernatant")
    left_pipette.pick_up_tip()
    left_pipette.aspirate(70, mag_plate["E1"], rate=0.02) # Or is even slower rate needed?
    left_pipette.dispense(70, reservoir["A1"].bottom(z=30))
    left_pipette.blow_out()
    left_pipette.drop_tip()
    right_pipette.pick_up_tip()
    protocol.delay(seconds=10)
    right_pipette.aspirate(20, mag_plate["E1"], rate=0.1) # Will this result in bead loss?
    right_pipette.drop_tip()

    protocol.comment("* Pre-heating heater to 37C in advance.")
    hs_mod.set_target_temperature(37)

    protocol.comment("* Washing beads with ethanol and dumping supernatant")
    for i in range(2): # Repeat once
        left_pipette.pick_up_tip()
        left_pipette.aspirate(200, falcon_tuberack["B3"]) # Height offset?
        left_pipette.dispense(200, mag_plate["E1"], rate=0.5)
        protocol.delay(seconds=10)
        left_pipette.aspirate(210, mag_plate["E1"], rate=0.02)
        left_pipette.air_gap(volume=30)
        left_pipette.dispense(240, reservoir["A1"].bottom(z=30))
        left_pipette.blow_out()
        left_pipette.drop_tip()

    right_pipette.pick_up_tip()
    right_pipette.aspirate(20, mag_plate["E1"], rate=0.1)
    right_pipette.drop_tip()

    protocol.comment("* Disengaging magnet and allowing bead to dry for 30 seconds.")
    mag_mod.disengage()
    protocol.delay(seconds=30)

    protocol.comment("* Resuspending beads in water, then moving to heater plate.")
    left_pipette.pick_up_tip()
    left_pipette.transfer(35, falcon_tuberack["A3"].bottom(z=60), mag_plate["E1"], new_tip="never")
    left_pipette.mix(10, 35, mag_plate["E1"])
    left_pipette.transfer(40, mag_plate["E1"], hs_plate["E10"], rate=0.5, new_tip="never")
    left_pipette.drop_tip()

    protocol.comment("* Making sure heater temperature is 37C")
    hs_mod.wait_for_temperature()

    protocol.comment("* Incubating sample on heater shaker at 37C for 10 minutes. Short shaking every 2 minutes.")    
    protocol.delay(minutes=2)
    for i in range(4): # Repeating this step 4 times
        hs_mod.set_and_wait_for_shake_speed(500) 
        protocol.delay(seconds=10)
        hs_mod.deactivate_shaker()
        protocol.delay(seconds=110)
    # Total time 10 minutes. (ignoring spinup time)
    hs_mod.deactivate_heater()

    protocol.comment("* Resuspending beads and moving sample to mag plate")
    left_pipette.pick_up_tip()
    left_pipette.mix(10, 35, hs_plate["E10"])
    left_pipette.aspirate(40, hs_plate["E10"], rate=0.5)
    left_pipette.dispense(40, mag_plate["E7"])
    left_pipette.blow_out()
    left_pipette.drop_tip()

    protocol.comment("* Engaging magnet for 7 minutes to pellet beads.")
    mag_mod.engage(height_from_base=8.5)
    protocol.delay(minutes=7)

    protocol.comment("* Extracting supernatant and placing in Eppendorf tube.")
    # ! In the future, put 1µL onto flexstation plate with qubit solution.

    left_pipette.transfer(199, falcon_tuberack["A1"].bottom(z=3), plate["C1"])

    right_pipette.pick_up_tip()
    right_pipette.aspirate(20, mag_plate["E7"], rate=0.1)
    right_pipette.dispense(19, ep_tuberack["A2"])
    right_pipette.dispense(1, plate["C1"])
    right_pipette.blow_out()
    right_pipette.drop_tip()
    protocol.delay(seconds=5)
    right_pipette.pick_up_tip()
    right_pipette.aspirate(15, mag_plate["E7"], rate=0.1)
    right_pipette.dispense(15, ep_tuberack["A2"])
    right_pipette.blow_out()
    right_pipette.drop_tip()

    
    left_pipette.pick_up_tip()
    left_pipette.mix(5, 100, plate["C1"])
    left_pipette.blow_out()
    left_pipette.drop_tip()

    hs_mod.open_labware_latch()