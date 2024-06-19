# Native Barcode Ligation protocols for Opentrons OT2

This file describes Opentrons protocols in the form of python scripts, and how to use them. A supplemental application is also described.
The comments in the python scripts explain the positioning of the modules, and which reagents are used and where they should be positioned.

## Opentrons OT2 scripts

The scripts 'DNArepFin.py', 'BarcodeLigationFin.py', and 'AdapterLigationFin.py' are adaptations of the first three parts from the Ligation sequencing gDNA - Native Bacoding Kit 24 V14 (SQK-NBD114.24). These have been cleaned up for more readability, but the exact scripts used in the last runs are also included in their own folder.

These parts need to be run in the order presented above, and will result in a DNA library that needs to be taken through the steps of the fourth part in the protocol 'Priming and Loading of the Flow Cell'. These scripts have been used to prepare a DNA library to be loaded into an Oxford Nanopore Flongle flow cell.
The scripts will assume that 2 samples are being sequenced.

NOTE: 
In between the runs of these protocols on the OT2 robot, the DNA sample has to be quantified. In particular it is completely necessary to do before 'BarcodeLigationFin.py', as it needs to know the sample concentrations early in the script in order to prepare equimolar volumes. 
By default these quantifications are intended to be done through the Flexstation plate reader, which needs standard measurements in addition to the sample itself to estimate the concentration.
Optionally, you can just run the sample+BR solution in a Qubit fluorometer.

NOTE:
I really recommend always doing a labware position check the day of the experiment, before you run any protocols.

## Qubit solution serial dilution for Flexstation standard curve

There is a separate protocol which prepares a serial dilution of calibration gDNA in Qubit Broad Range solution, 'flexstation_stdcurve_prep.py'. You may use this to fit a standard curve equation for calculating the spectral data of the plate reader to concentrations of DNA. (The plate has to be a black(non-opaque) corning well plate that fits both the OT2 labware slots and into the Flexstation plate reader).

In my tests, based on three replicates, I obtained the linear function:
> y = 0.1151x + 1.1604
In which x represents the spectral value from the plate reader of a well, and y represents the concentration of DNA in ng/µL.
You may make new replicates yourself by running 'flexstation_stdcurve_prep.py' on the OT2, and saving the read data from softmax and using that to create your standard curve / fitted line function. Softmax pro has the functionality to calculate a standard function and then use that to calculate the concentration itself, but I recommend creating a function based on multiple runs instead, in which case you also don'y need any specific settings when reading the plate to my knowledge.
If needed however, the .sda file I used is included.

There is functionality in BarcodeLigation.py to have the robot look for an exported flexstation txt file in jupyter notebook of the name 'DNArep_conc.txt', but this assumes that the concentration is already calculated and in the first two wells of the first plate column.
For now it is easier to input the concentrations manually at the beginning of the python script before running, but it wouldn't take much to update the file reading code in 'BarcodeLigationFin.py' to be able to read the export data in a better way.

## Application for file transfer onto the OT2 robot

I created a simple application selecting a file and uploading it to the OT2 Robot's Jupyter notebook file location.
The application is called on_gui. When you run its exe, it will attempt to find the MAC address of the usb-ethernet adapter (or is it the MAC address of the robot itself?) that has been used to connect the OT2 robot to the laptop in the robot lab. If it does, it will automatically enter its internal IP on the laptop. This MAC address is hardcoded, so if additional robots are to be used the code may need updating.
The application will open a user interface window where the IP can be manually edited. This window also gives the user the option to select a file on the computer to transfer to jupyter notebook. Once 'upload' has been clicked, the file should appear in the robots internal storage and now be accessible by any python scrips that try to open, read, or otherwise edit it.

I have let the pyinstaller promt window stay open together with the tkinter GUI window, so that it is easier to tell how the upload went.

The application requires that the laptop and OT2 robot have been set up for ssh file transfer, which I did according to Opentrons instructions: https://support.opentrons.com/s/article/Setting-up-SSH-access-to-your-OT-2

The exe file **must** have access to the ot2_ssh_key by it being in the same working directory. In the future, perhaps allow the user to select its location on the PC instead.

# Improvements & suggestions

- The DNA library preparation protocols would benefit from defining variables with the fluid names in the beginning of the scripts, and then referring to those in the pipetting commands for clarity.
- The DNA library preparation protocols are not very flexible. I suggest improving the GUI application to also allow the user to specify the number of samples, and having the python code dynamically adjust the positioning and reagents used for this. (Tip: Opentrons pipetting commands will simply be skipped if the volume is 0 that run)
- Currently all the library preparation protocols use the temperature module to keep the reagents cool at 4C. During my runs, I removed the reagents when they were used for the last time and moved them back to freezer storage. A more optimal solution could be to not use the reagents own tubes but move only the amount of fluid you need to specific eppendorf tubes, and then have the protocol deactivate the temperature module when the last reagent that needs cooling was used up. (This however adds more manual work time)
- The code that reads the read data from jupyter notebook in 'BarcodeLigationFin.py' only uses base python packages, hence why it looks for a .txt file instead of xls for example. I suggest instead exporting xls from Softmax pro, and using code in 'on_gui.py' to extract the relevant data and convert it into a csv format, and then have the python script on the OT2 read that once it has been uploaded to jupyter.
