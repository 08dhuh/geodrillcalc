# GeoDrillCalc - Geothermal Wellbore Parameter and Cost Calculation Tool for SGIL Project

GeoDrillCalc is a Python package for calculating wellbore parameters and estimating costs associated with drilling operations. The package uses input data about aquifer layers and initial parameters to output wellbore specifications and cost estimates. It's designed for use in various applications, including web applications and other software tools.

## Features
* **Aquifer Layer Analysis:** Determines the necessary wellbore specifications based on aquifer layers and depths.
* **Wellbore Specifications:** Calculates screen length, screen diameter, open hole diameter, and pump parameters.
* **Cost Estimation:** Provides detailed cost breakdowns including drilling rates, material costs, time rates, and other costs.
* **Output Format:** Results are provided as dictionaries, which can be easily converted to JSON or used directly in other applications.

## Installation

tbd

## Example Usage

A basic example of how to use GeoDrillCalc to calculate wellbore parameters and costs:

```python
import geodrillcalc.geodrillcalc_interface as gdc

# Define aquifer layer data (usually queried from a database)
aquifer_layer_table = {
    "aquifer_layer": [
        '100qa', '103utqd', '105utaf', '106utd', '107umta', 
        '108umtd', '109lmta', '111lta', '114bse'
    ],
    "is_aquifer": [True, False, True, False, True, False, True, True, False],
    "depth_to_base": [3, 53, 112, 150, 150, 1000, 1000, 1221, 1421]  # in metres
}

# Define initial values
initial_values = {
    "required_flow_rate": 4320,  # in litres per minute (L/min)
    "hydraulic_conductivity": 5,  # in metres per day (m/d)
    "average_porosity": 0.25,     # unitless (fractional)
    "bore_lifetime_year": 30,     # in years
    "groundwater_depth": 25,      # in metres
    "long_term_decline_rate": 1,  # in percentage per year (%/year)
    "allowable_drawdown": 25,     # in metres
    "safety_margin": 25,          # in percentage (%)
    "target_aquifer_layer": "109lmta", #the aquifer layer where the wellbore screen is installed. It’s the layer that you are primarily interested in extracting groundwater from or monitoring.
    "top_aquifer_layer": "100qa" #the uppermost aquifer layer
}

# Initialise GeoDrillCalcInterface instance
gci = gdc.GeoDrillCalcInterface()

# Calculate wellbore parameters and costs
wbd = gci.calculate_and_return_wellbore_parameters(
    is_production_well=False,  # pass True for production wells, False for injection wells
    aquifer_layer_table=aquifer_layer_table,
    initial_input_params=initial_values,
    cost_rates=None,  # Optional: Dictionary containing cost rates for different stages. If None, default rates are used.
    margin_rates=None  # Optional: Dictionary containing margin rates for different cost components. If None, default margins are used.
) 

# Check if calculations are ready
if wbd.ready_for_calculation and wbd.ready_for_installation_output and wbd.ready_for_cost_output:
    # Export results to dictionary
    result = wbd.export_results_to_dict()
    print(result)
else:
    print("Calculation is not ready.")
```

*Default Cost and Margin Rates*

If `cost_rates` or `margin_rates` are not provided in the `calculate_and_return_wellbore_parameters` function, GeoDrillCalc will use default values. These default cost and margin rates can be found in the configuration files located at:

- geodrillcalc/data/fallback_cost_rates.json
- geodrillcalc/data/fallback_margin_rates.json


*For information on aquifer codes and their definitions, refer to the [VVG Aquifer Codes](https://www.vvg.org.au/cb_pages/vaf.php).*

## Results

The `export_results_to_dict()` method returns a dictionary containing the wellbore specifications and cost estimates. Overview of the results:

### Installation Results

- **screen_length**: The length of the well screen (in metres).
- **screen_diameter**: The diameter of the well screen (in metres).
- **open_hole_diameter**: The diameter of the open hole (in metres).
- **pump_inlet_depth**: The depth at which the pump inlet is installed (in metres).
- **minimum_pump_housing_diameter**: The minimum diameter required for the pump housing (in metres).
- **casing_stage_table**: A table detailing the casing stages, including their top and bottom depths, casing diameter, and drill bit diameter.

### Cost Results

- **cost_estimation_table**: Provides a breakdown of estimated costs for various components and stages of the drilling process, including:
  - **stage**: The stage of the drilling process (e.g., drilling rates, materials, time rates, etc.).
  - **components**: The specific components within each stage (e.g., pilot hole, casing, etc.).
  - **low**, **base**, **high**: The estimated cost ranges (low, base, high) for each component.

- **total_cost_table**: Summarises the total estimated costs for each stage of the process and the overall total cost:
  - **drilling_rates**: Costs related to drilling operations.
  - **materials**: Costs of materials used in the drilling process.
  - **others**: Additional costs not included in the other categories.
  - **time_rates**: Costs associated with time-based factors (e.g., rig standby, accommodation).
  - **total_cost**: The combined total cost of all stages and components.

This detailed output allows users to understand the specifications of the wellbore and provides a comprehensive cost estimate for the drilling operation.

## Example Result

### Installation Results

- **screen_length**: `139.484` metres
- **screen_length_error**: `(125.536, 153.433)` metres
- **screen_diameter**: `0.1016` metres
- **open_hole_diameter**: `0.1905` metres
- **pump_inlet_depth**: `105` metres
- **minimum_pump_housing_diameter**: `0.286` metres

- **casing_stage_table(in metres)**:

| casing_stages         | top    | bottom | casing | drill_bit |
|-----------------------|--------|--------|--------|-----------|
| pre_collar            | 0.0    | 12.0   | 0.762  | 0.9144    |
| superficial_casing    | None   | None   | None   | None      |
| pump_chamber_casing   | None   | None   | None   | None      |
| intermediate_casing   | 0.0    | 990.0  | 0.1143 | 0.2159    |
| screen_riser          | 980.0  | 1000.0 | 0.1016 | 0.1905    |
| screen                | 1000.0 | 1139.0 | 0.1016 | 0.1905    |

### Cost Results

- **cost_estimation_table(in AUD)**:

| Stage            | Components                  | Low          | Base                        | High         |
|------------------|-----------------------------|--------------|-----------------------------|--------------|
| drilling_rates   | pilot_hole                  | None         | 210,804.58                  | None         |
| drilling_rates   | pre_collar                  | None         | 13,918.39                   | None         |
| drilling_rates   | superficial_casing          | None         | None                        | None         |
| drilling_rates   | pump_chamber_casing         | None         | None                        | None         |
| drilling_rates   | intermediate_casing         | None         | 62,038.28                   | None         |
| drilling_rates   | screen_riser                | None         | 455.33                      | None         |
| drilling_rates   | screen                      | None         | 3,164.57                    | None         |
| time_rates       | rig_standby_cost            | 1,600        | 1,800                       | 2,000        |
| time_rates       | development_bail_surge_jet  | 25,000.00    | 31,250.00                   | 37,500.00    |
| time_rates       | accommodation_cost          | 16,193.04    | 17,992.26                   | 19,791.49    |
| time_rates       | site_telehandler_cost       | 2,698.84     | 2,998.71                    | 3,298.58     |
| time_rates       | site_generator_fuel_cost    | 8,396.39     | 10,495.49                   | 12,594.58    |
| materials        | cement                      | 4,116.69     | 4,786.85                    | 5,457.01     |
| materials        | gravel                      | 204.79       | 238.13                      | 273.85       |
| materials        | bentonite                   | 3,328.05     | 3,697.83                    | 4,067.62     |
| materials        | drilling_fluid_and_lubricants | 5,145.34    | 5,717.04                    | 6,288.75     |
| materials        | drilling_mud                | 2,714.99     | 3,016.65                    | 3,318.32     |
| materials        | bore_flange_and_valve_spec  | 600          | 650                         | 700          |
| materials        | cement_shoe                 | 3,330.00     | 3,700.00                    | 4,070.00     |
| materials        | packer_lowering_assembly    | 4,680.00     | 5,200.00                    | 5,720.00     |
| materials        | pre_collar                  | 2,438.40     | 3,048.00                    | 3,657.60     |
| materials        | superficial_casing          | None         | None                        | None         |
| materials        | pump_chamber_casing         | None         | None                        | None         |
| materials        | intermediate_casing         | 313,121.44   | 354,552.94                  | 395,984.44   |
| materials        | screen_riser                | 5,440.41     | 6,277.41                    | 7,114.41     |
| materials        | screen                      | 38,218.96    | 44,036.11                   | 49,853.26    |
| materials        | centraliser                 | 4,910.00     | 8,546.13                    | 11,497.50    |
| others           | disinfection_drilling_plant | 1,500.00     | 1,500.00                    | 1,500.00     |
| others           | mobilisation_demobilization | 59,974.21    | 59,974.21                   | 59,974.21    |
| others           | installation_grouting_pre_collar | 3,600.00 | 3,600.00                    | 3,600.00     |
| others           | wireline_logging            | 11,280.89    | 12,534.33                   | 13,787.76    |
| others           | fabrication_installation    | 76,105.18    | 84,561.31                   | 93,017.45    |
| others           | cement_casing               | 38,785.46    | 48,481.82                   | 58,178.18    |
| others           | pack_gravel                 | 3,058.00     | 3,058.00                    | 3,058.00     |
| others           | subcontract_welders         | 10,795.36    | 11,994.84                   | 13,194.33    |

- **total_cost_table(in AUD)**:

| Stage            | Low           | Base            | High          |
|------------------|---------------|-----------------|---------------|
| drilling_rates   | 230,581.02    | 290,381.15      | 350,181.28    |
| materials        | 388,249.07    | 443,467.11      | 498,002.76    |
| others           | 205,099.10    | 225,704.51      | 246,309.92    |
| time_rates       | 53,888.27     | 64,536.46       | 75,184.65     |
| **total_cost**   | **877,817.46**| **1,024,089.23**| **1,169,678.62**|


**Notes:**

- Fields with `None` indicate components or stages that are not required for this particular well. For example, "superficial_casing" and "pump_chamber_casing" might not be needed based on the well design and geology.

- For `drilling_rates`, the total cost margins are considered with the pilot hole drilling cost margin times the total well depth. This provides an estimate based on the base cost of drilling a pilot hole adjusted for the well's depth.