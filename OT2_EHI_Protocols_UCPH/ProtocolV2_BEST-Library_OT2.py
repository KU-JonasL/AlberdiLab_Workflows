##########################
### BEST Library build ###
### V2 - 04092026 ###
##########################

## Author Jonas Greve Lauritsen
## Adaptation of the BEST library build.

#### Package loading ####
from opentrons import protocol_api
from math import *
import pandas as pd


#### User Input Parameters ###
def add_parameters(parameters):

    ## CSV file load
    #SampleNumber;WellPosition;EXBarcode;SampleID;DNAconc;DNAul;Waterul;Adaptor;Notes
    parameters.add_csv_file(
        variable_name = "AdaptorConc",
        display_name = "Adaptor Conc Input File",
        description = "csv file with adaptor concentration information"
    )

    ## Input Format
    parameters.add_str(
        variable_name="input_plate_type",
        display_name="Well plate type",
        choices=[{"display_name": "Covaris Plate", "value": "96afatubetpxplate_96_wellplate_200ul"},
        {"display_name": "PCR Plate", "value": "biorad_96_wellplate_200ul_pcr"}],
        default="96afatubetpxplate_96_wellplate_200ul"
    )


##################################

#### METADATA ####
metadata = {
    'protocolName': 'Protocol BEST Library Build - V2.0',
    'apiLevel': '2.28',
    'robotType': 'OT-2',    
    'author': 'Jonas Greve Lauritsen <jonas.lauritsen@sund.ku.dk>',
    'description': "Automated (BEST) library build of DNA samples (csv-adjusting version)."}


#### Protocol script ####
def run(protocol: protocol_api.ProtocolContext):

    #### Loading Protocol Runtime Parameters ####
    parsed_data = protocol.params.AdaptorConc.parse_as_csv()
    user_data = pd.DataFrame(parsed_data[1:], columns = parsed_data[0])
    Sample_Number = len(user_data[0])
    Column_Number = ceil(Sample_Number/8)


    #### LABWARE SETUP ####
    ## Smart labware; thermocycler and temperature modules.
    thermo_module = protocol.load_module('thermocyclerModuleV2')
    cold_module = protocol.load_module('temperature module', 9)


    ## Sample Plate (Placed in thermocycler).
    Sample_plate = thermo_module.load_labware('protocol.params.input_plate_type') ## Same plate as sat up for the purification.


    ## Mastermix Setup
    cold_plate = cold_module.load_labware('opentrons_96_aluminumblock_generic_pcr_strip_200ul')
    End_Repair_Mix = cold_plate.wells_by_name()["A1"]
    Adaptors_2mM = cold_plate.wells_by_name()["A4"]
    Adaptors_5mM = cold_plate.wells_by_name()["C4"]
    Adaptors_10mM = cold_plate.wells_by_name()["E4"]
    Adaptors_20mM = cold_plate.wells_by_name()["F4"]
    Ligation_Mix = cold_plate.wells_by_name()["A7"]
    Nick_Fill_In_Mix = cold_plate.wells_by_name()["A10"]


    ## Liquid/ Well Labeling
    ## ER
    ER_Liquid = protocol.define_liquid(name = "End Repair Mix", description = "End Repair Mix",display_color = "#0088FF")
    cold_plate.load_liquid(wells = ['A1','B1','C1','D1','E1','F1','G1','H1'], volume = (Column_Number*5.85*1.2), liquid = ER_Liquid) ## 20% overage

    ## Lig
    Lig_Liquid = protocol.define_liquid(name = "Ligation Mix", description = "Ligation Mix",display_color = "#FFE100")
    cold_plate.load_liquid(wells = ['A7','B7','C7','D7','E7','F7','G7','H7'], volume = (Column_Number*6*1.2), liquid = Lig_Liquid) ## 20% overage

    ## FI
    FI_Liquid = protocol.define_liquid(name = "Fill-In Mix",description = "Fill-In Mix",display_color = "#00EEFF")
    cold_plate.load_liquid(wells = ['A10','B10','C10','D10','E10','F10','G10','H10'], volume = (Column_Number*7.5*1.2), liquid = FI_Liquid) ## 20% overage

    ## Adaptors
    Adaptor2mM_Liquid = protocol.define_liquid(name = "Adaptors_2mM", description = "",display_color = "#FAADD7")
    cold_plate.load_liquid(wells = ['A4'], liquid = Adaptor2mM_Liquid)
    Adaptor5mM_Liquid = protocol.define_liquid(name = "Adaptors_5mM", description = "",display_color = "#F9587D")
    cold_plate.load_liquid(wells = ['C4'], liquid = Adaptor5mM_Liquid)
    Adaptor10mM_Liquid = protocol.define_liquid(name = "Adaptors_10mM", description = "",display_color = "#FF002B")
    cold_plate.load_liquid(wells = ['E4'], liquid = Adaptor10mM_Liquid)
    Adaptor20mM_Liquid = protocol.define_liquid(name = "Adaptors_20mM", description = "",display_color = "#EE00FF")
    cold_plate.load_liquid(wells = ['F4'], liquid = Adaptor20mM_Liquid)

    ## Samples
    Sample_Liquid = protocol.define_liquid(name = "Sample",description = "Library Sample",display_color = "#00FF37")
    Sample_plate.load_liquid(wells = Sample_plate.wells()[0:Sample_Number], volume = 50, liquid = Sample_Liquid)


    ## Tip racks (4x 10 µL)
    tiprack_10_1 = protocol.load_labware('opentrons_96_filtertiprack_10ul',4)
    tiprack_10_2 = protocol.load_labware('opentrons_96_filtertiprack_10ul',1)
    tiprack_10_3 = protocol.load_labware('opentrons_96_filtertiprack_10ul',2)
    tiprack_10_4 = protocol.load_labware('opentrons_96_filtertiprack_10ul',3)


    #### PIPETTE SETUP ####
    m20 = protocol.load_instrument('p20_multi_gen2', mount = 'right', tip_racks = [tiprack_10_1,tiprack_10_2,tiprack_10_3])
    p10 = protocol.load_instrument('p10_single', mount = 'left', tip_racks = [tiprack_10_4])

    
    ## Ligation height setup - to limit viscous solution on the outside of the tips.
    Ligation_height = [1.75, 1.6, 1.45, 1.30, 1.15, 1, 0.85, 0.70, 0.55, 0.4, 0.25, 0.10] ## List with volume height for 12 transfers and descending.
    pos = 12-Column_Number
    Ligation_height = Ligation_height[pos:] ## Removes highest, unused heights.




    ############################### Lab Work Protocol ###############################
    ## The instructions for the robot to execute.

    ## Initial activation of Smart Labware. Activate temperature module early in setup to reduce time waste.
    protocol.set_rail_lights(True)
    protocol.comment(f"STATUS: Library Building begun for {Sample_Number} samples.")
    protocol.comment("STATUS: Activating Modules")
    

    ## Activating smart modules
    cold_module.start_set_temperature(celsius = 10) ## 10 C for the temperature module as it preserves the solutions while reachable.
    thermo_module.open_lid()
    thermo_module.start_set_block_temperature(temperature = 10) ## 10 C to preserve samples and be reached.
    thermo_module.start_set_lid_temperature(temperature = 105) ## 105 C to avoid condensation formation in lid/ on seal.



    #### First step - End repair reaction ####
    ## step_group_ER = protocol.create_and_start_step_group( name="End Repair (ER)", description="Transfer liquid from reservoir to well plate") 
    protocol.comment("STATUS: End Repair Transfer Step Begun")

    ## Transfering End Repair Mix
    for i in range(Column_Number):
        Column= i*8
        m20.transfer(volume = 5.85, source = End_Repair_Mix, dest = Sample_plate.wells()[Column], mix_before = (2,10), mix_after = (5,10), new_tip = 'always', trash = False)

    
    ## End Repair Incubation
    protocol.comment("STATUS: End Repair Incubation Begun")
    thermo_module.close_lid()
    profile = [
        {'temperature':20, 'hold_time_minutes':30},
        {'temperature':65, 'hold_time_minutes':30}]
    thermo_module.execute_profile(steps = profile, repetitions = 1, block_max_volume = 30)
    thermo_module.set_block_temperature(10) ## Reset to 10 C while working
    thermo_module.open_lid()

    ## step_group_ER.end_group()


    #### Second step - Adaptors and Ligation ####
    ## step_group_LIG = protocol.create_and_start_step_group( name="Ligation (LIG)", description="Transfer Ligation mix to samples and incubate.")
    protocol.comment("STATUS: Adaptor Transfer Step Begun")

    ## Transferring Adaptors. The adaptor concentration is chosen based on the csv input using conditional logic.
    for i in range(Sample_Number):
        ## User data for adaptor selection
        #SampleNumber;WellPosition;EXBarcode;SampleID;DNAconc;DNAul;Waterul;Adaptor;Notes
        WellPosition = user_data['WellPosition'][i]
        AdaptorConc = int(user_data['Adaptor'][i])
        
        ## Transfer adaptor to sample well
        p10.pick_up_tip()
        if AdaptorConc == 2: ## 10 mM adaptor transfer
            p10.transfer(volume = 1.5, source = Adaptors_2mM, dest = Sample_plate.wells_by_name()[WellPosition], mix_before = (2,4), mix_after = (1,10), new_tip = 'never')
        if AdaptorConc == 5: ## 10 mM adaptor transfer
            p10.transfer(volume = 1.5, source = Adaptors_5mM, dest = Sample_plate.wells_by_name()[WellPosition], mix_before = (2,4), mix_after = (1,10), new_tip = 'never')
        if AdaptorConc == 10: ## 10 mM adaptor transfer
            p10.transfer(volume = 1.5, source = Adaptors_10mM, dest = Sample_plate.wells_by_name()[WellPosition], mix_before = (2,4), mix_after = (1,10), new_tip = 'never')
        if AdaptorConc == 20: ## 20 mM adaptor transfer
            p10.transfer(volume = 1.5, source = Adaptors_20mM, dest = Sample_plate.wells_by_name()[WellPosition], mix_before = (2,4), mix_after = (1,10), new_tip = 'never')
        else:
            protocol.comment(f"STATUS: {WellPosition} has an invalid Adaptor Concentration")


        p10.return_tip()


    ## Transfering Ligation Mix
    protocol.comment("STATUS: Ligation Transfer Step Begun")

    ## Changing flowrate for aspiration & dispension, as PEG4000 is viscous and requires slowed pipetting.
    m20.flow_rate.aspirate = 3 ## µL/s 
    m20.flow_rate.dispense = 3 ## µL/s

    ## Ligation Pipetting
    for i in range(Column_Number):
        ## Aspiration, mixing, and dispersion. Extra delays to allow viscous liquids to aspirate/dispense. Slow movements to limit adhesion.
        Column= i * 8
        m20.pick_up_tip()

        m20.move_to(location = Ligation_Mix.top())
        m20.move_to(location = Ligation_Mix.bottom(z = Ligation_height[i]), speed = 3)
        m20.mix(repetitions = 2, volume = 6, location = Ligation_Mix.bottom(z = Ligation_height[i]))
        m20.aspirate(volume = 6, location = Ligation_Mix.bottom(z = Ligation_height[i]))
        protocol.delay(10)
        m20.move_to(location = Ligation_Mix.top(), speed = 3)

        m20.dispense(volume = 6, location = Sample_plate.wells()[Column])
        m20.mix(repetitions = 3, volume = 10, location = Sample_plate.wells()[Column])
        protocol.delay(5)
        m20.move_to(location = Sample_plate.wells()[Column].top(), speed = 3)

        m20.return_tip()

    ## Ligation Incubation
    protocol.comment("STATUS: Ligation Incubation Step Begun")
    thermo_module.close_lid()
    profile = [
        {'temperature':20, 'hold_time_minutes':30},
        {'temperature':65, 'hold_time_minutes':10}]
    thermo_module.execute_profile(steps = profile, repetitions = 1, block_max_volume = 37.5)
    thermo_module.set_block_temperature(10) ## Reset to 10 C while working
    thermo_module.open_lid()

    ## step_group_LIG.end_grou()

    ### Third step - Fill-In Reaction ###

    ## step_group_FI = protocol.create_and_start_step_group(name = "Fill-In (FI)", description = "Transfer FI to samples andincubate")
    ## Transfering Fill-In reaction mix
    protocol.comment("STATUS: Fill-In Step Begun")
    
    ## Changing flowrate for aspiration & dispension to default (7.6 µL/s for 20 µL multichannel pipettes).
    m20.flow_rate.aspirate = 7.6 ## µL/s
    m20.flow_rate.dispense = 7.6 ## µL/s

    ## Fill-in Reaction pipetting
    for i in range(Column_Number):
        Column= i*8
        m20.transfer(volume = 7.5, source = Nick_Fill_In_Mix, dest = Sample_plate.wells()[Column], mix_before=(2,10), mix_after=(5,10), new_tip='always', trash = False)

    ## Fill-In Incubation
    protocol.comment("STATUS: Fill-In Incubation Step Begun")
    thermo_module.close_lid()
    profile = [
        {'temperature':65, 'hold_time_minutes':15},
        {'temperature':80, 'hold_time_minutes':15}]
    thermo_module.execute_profile(steps = profile, repetitions = 1, block_max_volume = 45)
    thermo_module.deactivate_lid() ## Turns off lid
    thermo_module.set_block_temperature(10) ## Reset to 10 C while working
    thermo_module.open_lid()

    ## step_group_FI.end_group()

    ### Protocol finished ###
    protocol.set_rail_lights(False)
    protocol.pause("STATUS: Protocol Completed.")

    ## Shuts down modules
    thermo_module.deactivate()
    cold_module.deactivate()
