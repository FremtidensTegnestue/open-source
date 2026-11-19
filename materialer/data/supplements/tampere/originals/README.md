# Dataset of hygrothermal measurements of 56 timber-framed wall structures and material properties

This dataset includes laboratory measurements of 56 different timber-framed wall structures for autumn, winter, and spring seasons, along with corresponding material properties. The dataset is sufficient for a typical hygrothermal software validation and benchmarking.

Information includes, for example, geometry, temperature, relative humidity, both initial and boundary values, and material properties that vary with relative humidity. The detailed list of the variables is given below in the "Structure" section. Long, descriptive variable names are used to minimize the need for separate documentation.

The data is primarily machine-readable to support large-scale simulation program validation, but remains accessible to humans. Common web browsers and text editors can open the JSON-files. Examples of accessing the data with Python are provided in "src" folder. JSON is the primary format, supplemented by additional images and XLSX files containing some of the same data. Material properties are also provided as TXT files for easy COMSOL readability.

Some files are repeated at the top level for easy preview on the Zenodo webpage.

## Authors
This dataset is compiled from multiple sources inside the research group (below) since 1999. The original authorship of the individual datapoints is not clear. While the main attributers of making the dataset public are listed below, this should be seen as a group effort.

Tampere University, Finland
Building Physics Research Group
Antti Mikkonen
Reseacher
antti.mikkonen@tuni.fi
Juha Vinha
Professor
juha.vinha@tuni.fi


## License:
This dataset and associated files are licensed under a Creative Commons Attribution 4.0 International License. To view a copy of this license, visit http://creativecommons.org/licenses/by/4.0/. This license allows others to share, remix, tweak, and build upon your work, even for commercial purposes, as long as they credit the original creation.

## Citing
Please cite both the Zenodo link [TODO!] and assosiated journal article [TODO!].

## Structure

### Material properties

Material properties are located in the "materialProperties" directory. All material properties are provided in a single file, allMaterialProperties.json, and also individually in folders named after the material index and type (e.g., A1_Gypsum_board).

To illustrate the format, the JSON file structure is shown below for A1_Gypsum_board.json; all others follow the same format. The structure includes general information, such as category and source, as well as material properties. Each material property's unit is indicated with the "_unit" extension. For example: "density" and "density_unit".

Additionally, many material properties vary with relative humidity. Such material properties are given as lists, and the corresponding relative humidity is given with a "_relative_humidity" extension. For example: "sorption_moisture_content" and "sorption_moisture_content_relative_humidity". Interpolation or curve fitting is recommended, see "src" for Python examples.

Alternatively, the table materialProperties.xlsx contains the same data in a slightly different format. The sources are also listed in this file.

The "forComsol" folder contains the same data as in the JSON files in a format suitable for COMSOL Multiphysics software.

### Wall structures

Wall structure measurement data is located in "wallStructures" dictionary. Schematics of the structures are given in schematics.pdf. Full wall asemblies are given in "assembly" subdictionary. Assemlies are given an assembly_id, for example: "1". 

Each assembly contain 4 different wall structures. The data for each wall structure is given both in the assembly JSON file and individually in "structure" dictionary. Each structure is given a "structure_id", for example "1a" or "1b". The "a" refers to a storage relative humidity of 56% and "b" to a storage relative humidity of 86%. The structures were stored in about +23C. Due to the installation time, the measurement initial conditions do not exactly match the storage conditions. For ease of use, initial conditions were calculated from the measured prope and boundary conditions as suitable averages and listed with the "initial" keyword. The initial conditions were not directly measured.

Hierarcical structure is used for the data. Using the Python syntax, the frame boundary ventilation cavity relative humidity is
    assembly["frame"]["boundary"]["ventilation_cavity_relative_humidity"]
using unit (no unit, 0.3 is 30%RH )
    assembly["frame"]["boundary"]["ventilation_cavity_relative_humidity_unit"]
given at times
    assembly["frame"]["boundary"]["time"]
using unit (s)
    assembly["frame"]["boundary"]["time_unit"]

Similarly for one of the wall structures the boundary indoor temperature is
    assembly["structure"]["upper_left_viewed_from_outside"]["boundary"]["indoor_temperature"]
using unit (degC)
    assembly["structure"]["upper_left_viewed_from_outside"]["boundary"]["indoor_temperature_unit"]
given at times
    assembly["structure"]["upper_left_viewed_from_outside"]["boundary"]["time"]
using unit (s)
    assembly["structure"]["upper_left_viewed_from_outside"]["boundary"]["time_unit"]

The individual structure JSON files in "structure" dictionary do not contain the information on the full assembly and the hierachy is simpler. For example the structure the boundary indoor temperature is
    structure["boundary"]["indoor_temperature"]

Using Python, the available keywords at each level are listed as
    assembly["structure"].keys()
or you can read them from the "Directory and JSON tree" section below. 

If you are familiar with Python and object oriented programming, using a dummy class to convert the Python dicts into objects might be more convinient. Maybe convert the lists to numpy arrays at the same time.

### Python code examples

Python examples for loading and using the data can be found in src.

### Directory and JSON tree


dataset
├── materialProperties
│   ├── A1_Gypsum_board_9mm
│   │   ├── A1_Gypsum_board_9mm.json
│   │   │   ├── category
│   │   │   ├── material_type
│   │   │   ├── product_name
│   │   │   ├── manufacturer
│   │   │   ├── id
│   │   │   ├── source
│   │   │   ├── note
│   │   │   ├── lisence
│   │   │   ├── original_source
│   │   │   ├── density
│   │   │   ├── density_unit
│   │   │   ├── thickness
│   │   │   ├── thickness_unit
│   │   │   ├── water_capillary_absorption_coefficient
│   │   │   ├── water_capillary_absorption_coefficient_unit
│   │   │   ├── specific_heat_capacity
│   │   │   ├── specific_heat_capacity_unit
│   │   │   ├── porosity
│   │   │   ├── porosity_unit
│   │   │   ├── sorption_moisture_content
│   │   │   ├── sorption_moisture_content_unit
│   │   │   ├── sorption_moisture_content_relative_humidity
│   │   │   ├── sorption_moisture_content_relative_humidity_unit
│   │   │   ├── adsorption_moisture_content
│   │   │   ├── adsorption_moisture_content_unit
│   │   │   ├── adsorption_moisture_content_relative_humidity
│   │   │   ├── adsorption_moisture_content_relative_humidity_unit
│   │   │   ├── desorption_moisture_content
│   │   │   ├── desorption_moisture_content_unit
│   │   │   ├── desorption_moisture_content_relative_humidity
│   │   │   ├── desorption_moisture_content_relative_humidity_unit
│   │   │   ├── moisture_diffusivity
│   │   │   ├── moisture_diffusivity_unit
│   │   │   ├── moisture_diffusivity_relative_humidity
│   │   │   ├── moisture_diffusivity_relative_humidity_unit
│   │   │   ├── moisture_diffusivity_adsorption
│   │   │   ├── moisture_diffusivity_adsorption_unit
│   │   │   ├── moisture_diffusivity_adsorption_relative_humidity
│   │   │   ├── moisture_diffusivity_adsorption_relative_humidity_unit
│   │   │   ├── thermal_conductivity
│   │   │   ├── thermal_conductivity_unit
│   │   │   ├── thermal_conductivity_relative_humidity
│   │   │   ├── thermal_conductivity_relative_humidity_unit
│   │   │   ├── water_vapour_diffusion_resistance_factor
│   │   │   ├── water_vapour_diffusion_resistance_factor_unit
│   │   │   ├── water_vapour_diffusion_resistance_factor_relative_humidity
│   │   │   ├── water_vapour_diffusion_resistance_factor_relative_humidity_unit
│   │   │   ├── water_vapour_permeability_with_respect_to_humidity_by_volume
│   │   │   ├── water_vapour_permeability_with_respect_to_humidity_by_volume_unit
│   │   │   ├── water_vapour_permeability_with_respect_to_humidity_by_volume_relative_humidity
│   │   │   ├── water_vapour_permeability_with_respect_to_humidity_by_volume_relative_humidity_unit
│   │   │   ├── water_vapour_permeability_with_respect_to_partial_water_vapour_pressure
│   │   │   ├── water_vapour_permeability_with_respect_to_partial_water_vapour_pressure_unit
│   │   │   ├── water_vapour_permeability_with_respect_to_partial_water_vapour_pressure_relative_humidity
│   │   │   └── water_vapour_permeability_with_respect_to_partial_water_vapour_pressure_relative_humidity_unit
│   │   ├── forComsol
│   │   │   ├── Aw.txt
│   │   │   ├── cp.txt
│   │   │   ├── delta_p.txt
│   │   │   ├── Dw.txt
│   │   │   ├── Dw_ad.txt
│   │   │   ├── Dw_de.txt
│   │   │   ├── k.txt
│   │   │   ├── rho.txt
│   │   │   ├── wc.txt
│   │   │   ├── wc_ad.txt
│   │   │   ├── wc_cap.txt
│   │   │   └── wc_de.txt
│   │   ├── A1_Gypsum_board_9mm_Moisture_diffusivity.pdf
│   │   ├── A1_Gypsum_board_9mm_Sorption.pdf
│   │   ├── A1_Gypsum_board_9mm_Thermal_conductivity.pdf
│   │   └── A1_Gypsum_board_9mm_Vapour_diffusivity.pdf
│   ├── other materials...
│   │   ├── ...
│   │   └── ...
│   ├── allMaterialProperties.json
│   │   ├── A1_Gypsum_board_9mm
│   │   │   ├── same structure as above for single material...
│   │   └── other materials...
│   └── materialProperties.xlsx
├── wallStructures
│   ├── schematics.pdf
│   ├── structure
│   │   ├── structure1a.json
│   │   │   ├── structure_id
│   │   │   ├── assembly_id
│   │   │   ├── layer_material_id
│   │   │   ├── layer_material_type
│   │   │   ├── material_thickness
│   │   │   ├── material_thickness_unit
│   │   │   ├── storage
│   │   │   │   ├── temperature
│   │   │   │   ├── temperature_unit
│   │   │   │   ├── relative_humidity
│   │   │   │   └── relative_humidity_unit
│   │   │   ├── initial
│   │   │   │   ├── temperature
│   │   │   │   ├── temperature_unit
│   │   │   │   ├── relative_humidity
│   │   │   │   └── relative_humidity_unit
│   │   │   ├── boundary
│   │   │   │   ├── time
│   │   │   │   ├── time_unit
│   │   │   │   ├── indoor_temperature
│   │   │   │   ├── indoor_temperature_unit
│   │   │   │   ├── indoor_relative_humidity
│   │   │   │   ├── indoor_relative_humidity_unit
│   │   │   │   ├── ventilation_cavity_temperature
│   │   │   │   ├── ventilation_cavity_temperature_unit
│   │   │   │   ├── ventilation_cavity_relative_humidity
│   │   │   │   └── ventilation_cavity_relative_humidity_unit
│   │   │   └── probe
│   │   │       ├── time
│   │   │       ├── time_unit
│   │   │       ├── insulation_surface_indoor_side_temperature
│   │   │       ├── insulation_surface_indoor_side_temperature_unit
│   │   │       ├── insulation_surface_indoor_side_relative_humidity
│   │   │       ├── insulation_surface_indoor_side_relative_humidity_unit
│   │   │       ├── insulation_surface_outdoor_side_temperature
│   │   │       ├── insulation_surface_outdoor_side_temperature_unit
│   │   │       ├── insulation_surface_outdoor_side_relative_humidity
│   │   │       ├── insulation_surface_outdoor_side_relative_humidity_unit
│   │   │       ├── varying_location_temperature
│   │   │       ├── varying_location_temperature_unit
│   │   │       ├── varying_location_relative_humidity
│   │   │       ├── varying_location_relative_humidity_unit
│   │   │       ├── coordinate_system
│   │   │       ├── insulation_surface_indoor_side_location
│   │   │       ├── insulation_surface_indoor_side_location_unit
│   │   │       ├── insulation_surface_outdoor_side_location
│   │   │       ├── insulation_surface_outdoor_side_location_unit
│   │   │       ├── varying_location
│   │   │       └── varying_location_unit
│   │   └── other structures...
│   ├── assembly
│   │   ├── assembly1.json
│   │   │   ├── assembly_id
│   │   │   ├── frame
│   │   │   │   ├── storage
│   │   │   │   │   ├── temperature
│   │   │   │   │   ├── temperature_unit
│   │   │   │   │   ├── relative_humidity
│   │   │   │   │   └── relative_humidity_unit
│   │   │   │   ├── initial
│   │   │   │   │   ├── temperature
│   │   │   │   │   ├── temperature_unit
│   │   │   │   │   ├── relative_humidity
│   │   │   │   │   └── relative_humidity_unit
│   │   │   │   ├── boundary
│   │   │   │   │   ├── time
│   │   │   │   │   ├── time_unit
│   │   │   │   │   ├── indoor_temperature
│   │   │   │   │   ├── indoor_temperature_unit
│   │   │   │   │   ├── indoor_relative_humidity
│   │   │   │   │   ├── indoor_relative_humidity_unit
│   │   │   │   │   ├── ventilation_cavity_temperature
│   │   │   │   │   ├── ventilation_cavity_temperature_unit
│   │   │   │   │   ├── ventilation_cavity_relative_humidity
│   │   │   │   │   └── ventilation_cavity_relative_humidity_unit
│   │   │   │   └── material
│   │   │   │       ├── beam_material_id
│   │   │   │       ├── beam_material_type
│   │   │   │       ├── inner_shell_material_id
│   │   │   │       ├── inner_shell_material_type
│   │   │   │       ├── outer_shell_material_id
│   │   │   │       └── outer_shell_material_type
│   │   │   └── structure
│   │   │       ├── upper_left_viewed_from_outside
│   │   │       │   └── same structure as above for single structure...
│   │   │       ├── upper_right_viewed_from_outside
│   │   │       │   └── same structure as above for single structure...
│   │   │       ├── lower_left_viewed_from_outside
│   │   │       │   └── same structure as above for single structure...
│   │   │       └── lower_right_viewed_from_outside
│   │   │           └── same structure as above for single structure...
│   │   └── other assemblies...
│   ├── fig
│   │   ├── structure1a.png (temperature and relative humidity plots)
│   │   └── ...
│   └── src
│       ├── codeExamplesForMaterialProperties.py
│       └── codeExamplesForWallStructures.py
└── README.md