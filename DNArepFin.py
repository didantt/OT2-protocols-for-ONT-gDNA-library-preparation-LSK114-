from opentrons import protocol_api, types


metadata = {
    "apiLevel": "2.16",
    "protocolName": "NBD1: DNA repair & end-prep",
    "description": """First part of the SQK-NBD114.24 Nanopore protocol. Uses same reagents. Protocol assumes kit tubes are used.""",
    "author": "Didrik Anttila"
    }

""" Material requirements

DNA: DNA samples (either 1 but 2 replicates, or 2 unique)
DCS: DNA Control Sample
AXP: AXP beads 
EB: Elution Buffer
UII: NEBNext Ultra II End Prep Enzyme mix
Ub: NEBNext Ultra II End Prep Reaction Buffer
RM: NEBNext FFPE DNA Repair Mix
RB: NEBNext FFPE DNA Repair Buffer
H2O: de-ionized milliQ water
Eth: 96% Ethanol
QB: Invitrogen 1X dsDNA BR Working Solution

Positioning in labware

Ep tuberack
A1: AXP 
A2: 1.5mL Eppendorf
A3: 1.5mL Eppendorf

Temperature module
A1: DNA ((400-1000ng))
A2: DNA ((400-1000ng))
A3: DCS ((1µL))
B1: RM ((0.5µL))
B2: UII ((0.75µL))
C1: RB ((0.875µL))
C2: Ub ((0.875µL))
C3: EB ((105µL))
D1: 1.5mL Eppendorf
D2: 1.5mL Eppendorf

Falcon tube rack
A1: QB ((3-4mL?))
A3: H2O ((? nearly full))
B3: 80% Eth ((Near empty or empty))
B4: 96% Eth ((Near full))
"""

# FSC454
sample1_conc = 296 # ng/µL

# FSC454
sample2_conc = 296 # ng/µL

# Because less than 4 barcodes, 1000ng used. (if more than 4, use 400ng)
sample1_vol = round(1000.0/sample1_conc, 1)
sample2_vol = round(1000.0/sample2_conc, 1)

# Whether to dilute DCS with Elution buffer. Leave only as True if fresh DCS tube without Elution buffer added to it.
# Pre-diluted tube should have a minimum of 1µL per sample. 
dilute_DCS = True

num_samples = 2
if num_samples not in range(1, 24):
    raise Exception("Number of samples not between 1 and 24.")



def run(protocol: protocol_api.ProtocolContext):
    # Labware
    big_tips = protocol.load_labware("opentrons_96_tiprack_300ul", 8) 
    small_tips = protocol.load_labware("opentrons_96_tiprack_20ul", 4)
    reservoir = protocol.load_labware("nest_1_reservoir_290ml", 5) 
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", 2) 
    ep_tuberack = protocol.load_labware("opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap", 10)
    falcon_tuberack = protocol.load_labware("opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical", 6)

    # Hardware modules
    hs_mod = protocol.load_module(
        module_name="heaterShakerModuleV1", 
        location="1")
    hs_adapter = hs_mod.load_adapter(
        "opentrons_96_pcr_adapter") 
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

    # User check before starting
    protocol.pause(f"Sample concentrations are {sample1_conc} and {sample2_conc}, and their volumes are {sample1_vol} and {sample2_vol}. Does that seem correct?")
    protocol.pause(f"Diluting DCS is set to {dilute_DCS}, is that correct?")

    # Assumes beads in eppendorf tube in slot A1 were suspended immediately before starting the protocol.
    protocol.comment("* Adding SUSPENDED beads to heater shaker wells")

    left_pipette.pick_up_tip()
    left_pipette.aspirate(50, ep_tuberack["A1"], rate=0.5) # Reactant tube
    left_pipette.default_speed = 100
    left_pipette.touch_tip(ep_tuberack["A1"], radius=0.6, speed=2)
    left_pipette.touch_tip(ep_tuberack["A1"], radius=0.6, speed=2)
    left_pipette.air_gap(volume=10)
    left_pipette.dispense(60, hs_plate["H1"])
    left_pipette.blow_out()
    left_pipette.drop_tip()
    left_pipette.default_speed = 400


    temp_mod.set_temperature(celsius=4) # The protocol will wait for the temperature to be reached before proceeding, omit this step while testing.
    protocol.comment(f"* Temperature module now 4C. The number of samples is {num_samples}")


    
    # Thaw AXP & DCS @ RT. Will assume this is done manually.
    # skip to Dilute DCS with EB

    
    if dilute_DCS == True: # Set to false if you already have some
        protocol.comment("* Diluting DCS with 105uL Elution buffer...")
        #protocol.max_speeds['x'] = 20
        left_pipette.transfer(105, temp_labware["C3"], temp_labware["A3"].bottom(z=18), rate=0.5, mix_after=(4, 105)) 
        #del protocol.max_speeds['x']

    # Add DNA sample & water to 11µL. ! (User must give the volume of sample)
    

    ############# The part of the protocol where the sample reaction mixture is made and handled before pelletting (This is the part where I am not sure what procedure is appropriate)
    


    # Multiply this 2-fold instead.
    # if num_samples > 8:
    #     mmix_factor = num_samples
    # else:
    #     mmix_factor = 8
    mmix_factor = num_samples

    mmix_tot_vol = mmix_factor * float(1+0.875+0.875+0.75+0.5)




    # # Make sample master mix. Doing 8fold mix to avoid sub-1uL volume (which the pipette can't handle accurately).
    protocol.comment(f"* Forgoing making DNA sample elution master mix by directly mixing it in the plate wells. Enough for {mmix_factor} samples)") 


    # non-dynamic version, removes need for falcon tuberack A1.
    #-Gets and dispenses DCS
    right_pipette.pick_up_tip()
    right_pipette.mix(5, 20, temp_labware["A3"].bottom(z=18))
    right_pipette.blow_out()
    right_pipette.aspirate(2*1, temp_labware["A3"].bottom(z=18), rate=0.5) # Reactant tube
    right_pipette.dispense(1, hs_plate["A1"], rate=0.5)
    right_pipette.dispense(1, hs_plate["A2"], rate=0.5)
    right_pipette.drop_tip()
    #-Gets and dispenses Repair buffer
    right_pipette.pick_up_tip()
    right_pipette.mix(5, 20, temp_labware["C1"])
    right_pipette.blow_out()
    right_pipette.aspirate(2*0.875, temp_labware["C1"], rate=0.5) # Reactant tube
    right_pipette.dispense(0.875, hs_plate["A1"], rate=0.5) # It's uncertain if the robot can dispense these volumes with sufficient accuracy.
    right_pipette.dispense(0.875, hs_plate["A2"], rate=0.5)
    right_pipette.drop_tip()
    #-Gets and dispenses End-prep buffer
    right_pipette.pick_up_tip()
    right_pipette.mix(5, 20, temp_labware["C2"])
    right_pipette.blow_out()
    right_pipette.aspirate(2*0.875, temp_labware["C2"], rate=0.5) # Reactant tube
    right_pipette.dispense(0.875, hs_plate["A1"], rate=0.5)
    right_pipette.dispense(0.875, hs_plate["A2"], rate=0.5)
    right_pipette.drop_tip()
    #-Gets and dispenses Ultra II
    right_pipette.pick_up_tip()
    right_pipette.mix(10, 20, temp_labware["B2"])
    right_pipette.blow_out()
    right_pipette.aspirate(2*0.75, temp_labware["B2"], rate=0.5) # Reactant tube
    right_pipette.dispense(0.75, hs_plate["A1"], rate=0.5)
    right_pipette.dispense(0.75, hs_plate["A2"], rate=0.5)
    right_pipette.drop_tip()
    #-Gets and dispenses FFPE DNA Repair mix
    right_pipette.pick_up_tip()
    right_pipette.mix(10, 20, temp_labware["B1"])
    right_pipette.blow_out()
    right_pipette.aspirate(2*0.5, temp_labware["B1"], rate=0.5) # Reactant tube
    right_pipette.dispense(0.5, hs_plate["A1"], rate=0.5)
    right_pipette.dispense(0.5, hs_plate["A2"], rate=0.5)
    right_pipette.drop_tip()



    protocol.comment(f"* Moving DNA samples to HS, and adding water to samples to a total of 11uL.")



    right_pipette.transfer(
        int(11-sample1_vol), 
        falcon_tuberack["A3"].bottom(z=70), 
        hs_plate["A1"]
    ) 
    right_pipette.transfer(
        int(11-sample2_vol), 
        falcon_tuberack["A3"].bottom(z=70), 
        hs_plate["A2"]
    ) 
    
    right_pipette.transfer(sample1_vol, temp_labware["A1"], hs_plate["A1"], mix_after=(4, 6), blow_out=True) 
    right_pipette.transfer(sample2_vol, temp_labware["A1"], hs_plate["A2"], mix_after=(4, 6), blow_out=True) 

    # Should use a thermal cycler for this, but in the meantime will code for heater shaker.

    protocol.comment("* Initiating incubation. 5 min at RT, then 5 min at 65C.")
    
    protocol.delay(minutes=5)
    hs_mod.set_target_temperature(65)
    hs_mod.wait_for_temperature()
    protocol.delay(minutes=5)
    hs_mod.deactivate_heater()
    
    protocol.comment("* Transferring mixture to eppendorf tubes, and suspending beads.")
    right_pipette.transfer(15+5, hs_plate["A1"], ep_tuberack["A2"], rate=0.7)
    right_pipette.transfer(15+5, hs_plate["A2"], ep_tuberack["A3"], rate=0.7)

    hs_mod.set_and_wait_for_shake_speed(900)
    protocol.delay(seconds=2)
    hs_mod.deactivate_shaker()

    protocol.comment("* Transferring 15uL suspended AXP beads to samples. Mixing.")
    
    
    
    left_pipette.pick_up_tip()

    for tube in [ep_tuberack["A2"], ep_tuberack["A3"]]:
        
        left_pipette.mix(3, 30, hs_plate["H1"])
        left_pipette.blow_out()
        left_pipette.touch_tip(hs_plate["H1"], radius=0.85, v_offset=-2, speed=3)
        
        right_pipette.pick_up_tip()
        right_pipette.aspirate(15, hs_plate["H1"], rate=0.5)
        right_pipette.default_speed = 100
        #right_pipette.air_gap(volume=5)
        right_pipette.touch_tip(hs_plate["H1"], radius=0.85, v_offset=-2, speed=3) # Perhaps greater radius needed to touch
        right_pipette.touch_tip(hs_plate["H1"], radius=0.85, v_offset=-2, speed=3)
        
        right_pipette.dispense(15, tube)
        right_pipette.default_speed = 400
        right_pipette.drop_tip()
        
    left_pipette.drop_tip()


    # Incubate on hula mixer for 5 min at RT (heater shaker)
    
    # Heater shaker + Pipette solution for this? Pipette mixing over time would cost too many pipette tips I think, if we have more than 1 sample.
    protocol.pause("PAUSE: Take eppendorf tubes from tuberack position A2 and A3, and incubate for 5 minutes on Hula mixer. Handle with care! Or take directly to flexstation for quantification if you want to skip the washing step, in which case cancel the run.")
    protocol.comment("* Incubate at RT for 5 min.")
    protocol.pause("PAUSE: Resume ONLY if you have reattached eppendorf tubes with mixture to tube rack positions A2 and A3.")    
    

    # Put sample on magnet. Should be 30µL at this point.
    mag_mod.engage(height_from_base=3.5) # 8.5 is the maximum engage height without raising the plate. 3.5 will make sure the pellet is close to the bottom.
    protocol.comment("* Engaging magnet, and putting samples on it.")
    left_pipette.transfer(30+5, ep_tuberack["A2"], mag_plate["A1"], blow_out=True)
    left_pipette.transfer(30+5, ep_tuberack["A3"], mag_plate["A2"], blow_out=True)
    
    protocol.delay(minutes=5)
    #################################################### End of the part of the protocol that handles the sample and reaction mixture
    # Alternative in the future could be to put plastic film on plate and put the entire film on hula mixer.



    # for 500µL 80% ethanol, we need 444 H2O & 55 96% Eth. # For two samples, double all of it!!!!
    # left_pipette.transfer(444, falcon_tuberack["B3"], falcon_tuberack["A3"]) ! This actually automatically divides this into multiple transfer steps.
    protocol.comment("* Per sample: transfer 444ul water to empty falcon tube, then add 56uL 96percent ethanol. Mix")
    
    left_pipette.transfer(num_samples*444, falcon_tuberack["A3"].bottom(z=60), falcon_tuberack["B3"].bottom(z=60))
    
    left_pipette.transfer(num_samples*55, falcon_tuberack["B4"].bottom(z=70), falcon_tuberack["B3"].bottom(z=60), mix_after=(3, 300)) # If volume greater than 300, it will contaminate the 96%eth


    protocol.comment("* Dumping supernatants before washing.")
    left_pipette.transfer(40, mag_plate["A1"], reservoir["A1"].bottom(z=30), rate=0.02)
    left_pipette.transfer(40, mag_plate["A2"], reservoir["A1"].bottom(z=30), rate=0.02)
    
    protocol.comment("* Washing pellets, and dumping supernatant.")
    
    # With offset to pipette directly onto pellets. 
    # Pellets form on the right side of wells of uneven number, and left side of wells of even number.
    for i in range(2): # Repeat once

        for mag_well in [mag_plate["A1"], mag_plate["A2"]]: # Once per well
            left_pipette.pick_up_tip()
            left_pipette.aspirate(200, falcon_tuberack["B3"]) # Height offset?
            left_pipette.dispense(200, mag_well)
            protocol.delay(seconds=10)
            left_pipette.aspirate(210, mag_well, rate=0.3)
            left_pipette.air_gap(volume=30)
            left_pipette.dispense(240, reservoir["A1"].bottom(z=30))
            left_pipette.blow_out()
            left_pipette.drop_tip()


    
    protocol.comment("* Allowing pellets to dry for 30 sec, then disengaging magnet.")
    protocol.delay(seconds=30)
    mag_mod.disengage()

    # No need to put samples on heater shaker, since only incubation is happening and the sample is going back to the magnet later anyway.
    # ! Unless? Beads will probably not be suspended from this pipette mixing.
    protocol.comment("* Resuspending pellet in 10uL water. Then incubating for 2 minutes at RT.") # Assuming room is RT
    # !!! Will the water level be high enough to touch the pellet? If not, consider lower magnet height.
    # ! Perhaps offset to splash on pellet?

    # !!! Something happened that caused different volumes in the two wells. What happened? How to prevent it?
    right_pipette.transfer(10, falcon_tuberack["A3"].bottom(z=60), mag_plate["A1"]) # Total volume about 15? No clue, evaluate through tests. 
    right_pipette.transfer(10, falcon_tuberack["A3"].bottom(z=60), mag_plate["A2"])

    # Resuspending beads via pip-mixing.
    for mag_well in [mag_plate["A1"], mag_plate["A2"]]:
        left_pipette.pick_up_tip()
        left_pipette.mix(6, 20, mag_well)
        left_pipette.blow_out()
        left_pipette.drop_tip()

    
    protocol.delay(minutes=0.2) # Perhaps subtract pipmixing time
    

    protocol.comment("* Re-engaging magnet, and allowing pellet to form for 5 minutes.")
    mag_mod.engage(height_from_base=8.5) # More magnet engagement is fine since we are now only interested in the eluate and no further washing will be done.
    protocol.delay(minutes=5)
    
    protocol.comment("* Adding Broad Range Qubit solution to corning plate wells.")
    left_pipette.transfer(199, falcon_tuberack["A1"].bottom(z=3), [plate["A1"], plate["A2"]]) # Double check before running

    protocol.comment("* Putting 1ul eluted samples on flexstation plate for DNA quantification. (Position A1 & A2)") # ! Will be a flexstation plate.
    
    right_pipette.pick_up_tip()
    right_pipette.aspirate(10+5, mag_plate["A1"], rate=0.1) 
    
    protocol.comment("* Putting End-prepped DNA sample 1 in empty eppendorf in temp module.")
    right_pipette.dispense(10+5, temp_labware["D1"]) 
    right_pipette.mix(5, 5, temp_labware["D1"]) 
    right_pipette.blow_out()
    protocol.comment("* Adding 1uL to corning plate well A1.")
    right_pipette.aspirate(1, temp_labware["D1"])
    right_pipette.dispense(1, plate["A1"])
    right_pipette.blow_out()
    right_pipette.drop_tip()

    right_pipette.pick_up_tip()
    right_pipette.aspirate(10+5, mag_plate["A2"], rate=0.1) 

    
    protocol.comment("* Putting End-prepped DNA sample 2 in empty eppendorf in temp module.")
    right_pipette.dispense(10+5, temp_labware["D2"])
    right_pipette.mix(5, 5, temp_labware["D2"]) 
    right_pipette.blow_out()
    protocol.comment("* Adding 1uL to corning plate well A2.")
    right_pipette.aspirate(1, temp_labware["D2"])
    right_pipette.dispense(1, plate["A2"])
    right_pipette.blow_out()
    right_pipette.drop_tip()

    for well in [plate["A1"], plate["A2"]]:
        left_pipette.pick_up_tip()
        left_pipette.mix(5, 100, well)
        left_pipette.blow_out()
        left_pipette.drop_tip()


    mag_mod.disengage()
    hs_mod.open_labware_latch()
    # Now quantify that eluate plate in Flexstation.



    
