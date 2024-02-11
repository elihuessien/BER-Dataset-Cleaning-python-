#!/usr/bin/env python

"""--------------------
As per filter rule the calculated ground floor height should be greater than 2.39 m. 
However, the specific minimum average ceiling height requirements can vary depending on the country 
or region's building codes and regulations. However, some common guidelines or standards are often 
followed. In the UK, for example, the Building Regulations Approved Document B (Fire Safety) provides 
guidance on this matter.

As of my last knowledge update in September 2021, the UK Building Regulations specify the following requirements
 for areas with sloping ceilings:

Minimum Height at the Eaves: The minimum height at the eaves (the lowest point of the sloping ceiling)
should be no less than 2.0 meters (approximately 6 feet 6 inches). This ensures that there is sufficient 
headroom near the sides of the room.

Minimum Average Ceiling Height: The average height of the sloping ceiling, measured along a line running 
horizontally, should be no less than 2.3 meters (approximately 7 feet 6 inches). This average height allows for a 
comfortable usable area in the center of the room.

In Ireland, building regulations are set out in the Building Control Regulations 1997-2018 and the Technical Guidance 
Document Part K (TGD K) - Stairways, Ladders, Ramps, and Guards. These regulations provide guidelines on various aspects 
of building construction, including ceiling heights and headroom requirements.

While TGD K in Ireland covers stairways, ladders, ramps, and guards, it does not specifically address sloping ceilings. 
The specific requirements for minimum average ceiling height in areas with sloping ceilings might be found in other sections 
of the Irish building regulations or in supplementary guidance documents.

To ensure compliance with Irish building regulations, it is essential to refer to the most current version of the Building 
Control Regulations and any relevant Technical Guidance Documents issued by the Department of Housing, Local Government, and 
Heritage in Ireland.

Standard door sizes 1981 * 762 (internal) and 1981 * 762, 1981 * 838, 2032 * 813 (external), however atleast one external 
door shoud be 914 mm  wide and 2032  mm tall (1.85). 
https://codes.iccsafe.org/s/IBC2018/chapter-10-means-of-egress/IBC2018-Ch10-Sec1010.1 (International residential code)
------------------------------------
"""

__author__ = "Elihu Essien-Thompson, Kumar Raushan"
__copyright__ = "Copyright 2023, The Irish Stock Observatory"
__credits__ = ["Ciara Ahern", "Mark Mulville", "Kumar Rushan",
                    "Chenlu Li", "Elihu Essien-Thompson"]
__license__ = "GNU GPLv3"
__version__ = "1.0.1"
__maintainer__ = "Elihu Essien-Thompson"
__email__ = "elihu.essienthompson@tudublin.ie"
__status__ = "Production"


from datetime import datetime
import pandas as pd
import csv

# Possible exception to be thrown
class FileAccessError(Exception):
    def __init__(self, message):
        super().__init__(message)



def convert_txt_to_csv(input_txt_file: str, output_csv_file: str) -> None:
    """
    Converting text file to CSV
    This function converts a txt file to csv while ensuring utf-8 encoding. 

    Args:
        input_csv_file (str): string path to '.txt' file
        output_csv_file (str): sting path to '.csv' file

    Returns:
        None
    
    Raises:
        FileNotFoundError: if file read fails
        FileAccessError: if the input or output file extension are not correct
    """
    # error checking
    if not (input_txt_file.endswith('.txt') or output_csv_file.endswith('.csv')):
        raise FileAccessError("The input file must be '.txt' and the output file must be '.csv'")
    

    # Open the TXT file for reading and the CSV file for writing
    with open(input_txt_file, 'r', encoding='utf-8', errors='replace') as txt_file, open(output_csv_file, 'w', newline='', encoding='utf-8') as csv_file:
        # Create a CSV writer
        csv_writer = csv.writer(csv_file)
        
        # Read each line from the TXT file and split it into fields 
        for line in txt_file:
            # Replace non-decodable characters with a placeholder 
            line = line.encode('utf-8', 'replace').decode('utf-8')
            
            fields = line.strip().split('\t')

            # Write the fields to the CSV file
            csv_writer.writerow(fields)
    
    print(f"Conversion from {input_txt_file} to {output_csv_file} completed.")





# Listed bellow are the functions to be applied to the dataset.
# Each function opperates at the row level and performs individual operations on the data
# and returns the edited row


def add_desired_columns(data_row: pd.Series) -> pd.Series:

    # Addititon 1 - DEAP Age Band
    bins = [float('-inf'), 1899, 1929, 1949, 1966, 1977, 1982, 1993, 1999, 2004, 2009, float('inf')]
    construction_period = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"]

    for i in range(len(bins)-1):
        if (data_row["Year_of_Construction"] > bins[i] and data_row["Year_of_Construction"] <= bins[i+1]):
            data_row['AgeBand'] = construction_period[i]
    

    # Addition 2 - Thermal Era
    data_row['ThermalEra'] = 'Pre' if(data_row['Year_of_Construction'] <= 1977) else 'Post'

    # Addition 3 - Glazing percentage
    data_row['GlazingPercent'] = (data_row['WindowArea'] / data_row['WallArea']) if (data_row['WallArea'] > 0) else 0

    # Addition 4 - Total Dwelling volume
    data_row['Volume'] = data_row['GroundFloorArea(sq m)'] * (data_row['GroundFloorHeight'] +data_row['FirstFloorHeight'] +data_row['SecondFloorHeight'] + data_row['ThirdFloorHeight'])
    
    return data_row




def drop_unwanted_columns(data_row: pd.Series) -> pd.Series:
    # There are errors within the description columns due to thier subjective nature
    # so it was decided that they be dropped
    columns_to_drop  = ['FirstWallDescription', 'SecondWallDescription', 'ThirdWallDescription']
    columns_to_drop += [col for col in data_row.index.tolist() if col.startswith('Unnamed:')]
    kept_rows        = [col for col in data_row.index.tolist() if col not in columns_to_drop]

    return data_row[kept_rows]


# This function contains any corrections for internal consistency that needs to be performed
def correct_column_data(data_row: pd.Series) -> pd.Series:
    # Correctly assign number of stories. Staring from 1 storey for a solo ground floor building.
    if data_row['NoStoreys'] < 4:
        data_row['NoStoreys'] = 1 + sum([1 for height in ['FirstFloorHeight','SecondFloorHeight','ThirdFloorHeight'] if data_row[height] > 0])
    
    return data_row
        


# This functions contains the criteria for row exclusion
def filter_by_criteria(data_row: pd.Series) -> bool:
    exclude_row = False     # This boolean will be triggered by any failing exclusion clause

    # -------- Independent Exclusion Clauses -------------
    # Clause 1 - Year of Construction
    if (data_row['Year_of_Construction'] > datetime.now().year): 
        exclude_row = True

    # Double check - The code below seems redundant
    # if (data_row['DoorArea'] == 0 or data_row['WindowArea'] == 0): exclude_row = True
    # QUery also the finall finding of door vs window area

    # 5 < Y < 10

    # Clause 2 - Ground Floor Height 
    if not((2.30 <= data_row['GroundFloorHeight']  <= 3.46) or
           data_row['GroundFloorHeight'] == 0): 
        exclude_row = True
    
    # Clause 3 - Type of Rating
    if not any(allowed_substring in data_row for allowed_substring in ['Final', 'Existing', 'Provisional']):
        exclude_row = True

    
    # Clause 4 - HS Main System Efficiency
    if not(data_row['HSMainSystemEfficiency'] == 0 or               # no bioler
           23.07 <= data_row['HSMainSystemEfficiency'] <= 95.90 or  # conventional boiler
           100   <= data_row['HSMainSystemEfficiency'] <= 635.34):  # prob. central heating system
        exclude_row = True

    # Clause 5 - WH Main System Efficiency
    if not(data_row['WHMainSystemEff'] == 0 or               # no bioler
           24   <= data_row['WHMainSystemEff'] <= 95.90 or   # conventional boiler
           100  <= data_row['WHMainSystemEff'] <= 389.9):    # prob. heat pumps
        exclude_row = True


    # -------- Case-dependent Exclusion Clauses ----------
    # Clauses 6 - 16
    match data_row['DwellingTypeDescr']:

        case 'Semi-detached house':
            if not (11.27   <= data_row['LivingAreaPercent']      <= 35.16 ): exclude_row = True
            if not (53.19   <= data_row['WallArea']               <= 147.96): exclude_row = True
            if not (31.13   <= data_row['FloorArea']              <= 119.09): exclude_row = True
            if not (48.75   <= data_row['GroundFloorArea(sq m)']  <= 186.83): exclude_row = True
            if not (32.34   <= data_row['RoofArea']               <= 127.39): exclude_row = True
            if not (7.09    <= data_row['WindowArea']             <= 41.99 ): exclude_row = True
            if not (0       <  data_row['DoorArea']               <= 5.86  ): exclude_row = True

        case 'End of terrace house':
            if not (12.96   <= data_row['LivingAreaPercent']      <= 59.49 ): exclude_row = True
            if not (56.62   <= data_row['WallArea']               <= 155.61): exclude_row = True
            if not (29.97   <= data_row['FloorArea']              <= 104.74): exclude_row = True
            if not (58.68   <= data_row['GroundFloorArea(sq m)']  <= 190.49): exclude_row = True
            if not (29.99   <= data_row['RoofArea']               <= 108.82): exclude_row = True
            if not (5.66    <= data_row['WindowArea']             <= 34.82 ): exclude_row = True
            if not (1.54    <= data_row['DoorArea']               <= 17.97 ): exclude_row = True

        case 'Detached house':
            if not (7.54    <= data_row['LivingAreaPercent']      <= 45.89 ): exclude_row = True
            if not (31.68   <= data_row['WallArea']               <= 336.19): exclude_row = True
            if not (28.87   <= data_row['FloorArea']              <= 255.60): exclude_row = True
            if not (52.24   <= data_row['GroundFloorArea(sq m)']  <= 422.20): exclude_row = True
            if not (30.08   <= data_row['RoofArea']               <= 290.85): exclude_row = True
            if not (5.61    <= data_row['WindowArea']             <= 83.48 ): exclude_row = True
            if not (0       <  data_row['DoorArea']               <= 6.28  ): exclude_row = True

        case 'Top-floor apartment':
            if not (-0.23   <= data_row['LivingAreaPercent']      <= 62.28 ): exclude_row = True
            if not (4.63    <= data_row['WallArea']               <= 139.35): exclude_row = True
            if not (0       <= data_row['FloorArea']              <= 0     ): exclude_row = True
            if not (18.29   <= data_row['GroundFloorArea(sq m)']  <= 153.06): exclude_row = True
            if not (12.16   <= data_row['RoofArea']               <= 126.58): exclude_row = True
            if not (2.02    <= data_row['WindowArea']             <= 38.71 ): exclude_row = True
            if not (0       <  data_row['DoorArea']               <= 1.91 ): exclude_row = True

        case 'Mid-terrace house':
            if not (13.03   <= data_row['LivingAreaPercent']      <= 72.13 ): exclude_row = True
            if not (29.24   <= data_row['WallArea']               <= 163.64): exclude_row = True
            if not (31.65   <= data_row['FloorArea']              <= 101.19): exclude_row = True
            if not (61.13   <= data_row['GroundFloorArea(sq m)']  <= 189.89): exclude_row = True
            if not (32.54   <= data_row['RoofArea']               <= 110.68): exclude_row = True
            if not (4.29    <= data_row['WindowArea']             <= 29.02 ): exclude_row = True
            if not (1.61    <= data_row['DoorArea']               <= 21.04 ): exclude_row = True

        case 'Maisonette':
            if not (6.39    <= data_row['LivingAreaPercent']      <= 78.28 ): exclude_row = True
            if not (20.88   <= data_row['WallArea']               <= 255.43): exclude_row = True
            if not (-3.65   <= data_row['FloorArea']              <= 841.0 ): exclude_row = True
            if not (12.82   <= data_row['GroundFloorArea(sq m)']  <= 182.30): exclude_row = True
            if not (-121.43 <= data_row['RoofArea']               <= 84.78 ): exclude_row = True
            if not (1.83    <= data_row['WindowArea']             <= 35.75 ): exclude_row = True
            if not (1.83    <= data_row['DoorArea']               <= 6.21 ): exclude_row = True

        case 'House':
            if not (6.61    <= data_row['LivingAreaPercent']      <= 39.73 ): exclude_row = True
            if not (57.96   <= data_row['WallArea']               <= 392.64): exclude_row = True
            if not (-8.56   <= data_row['FloorArea']              <= 248.01): exclude_row = True
            if not (53.63   <= data_row['GroundFloorArea(sq m)']  <= 453.75): exclude_row = True
            if not (-4.44   <= data_row['RoofArea']               <= 284.29): exclude_row = True
            if not (5.44    <= data_row['WindowArea']             <= 78.07 ): exclude_row = True
            if not (0       <  data_row['DoorArea']               <= 4.73  ): exclude_row = True

        case 'Apartment':
            if not (43.39   <= data_row['LivingAreaPercent']      <= 57.59 ): exclude_row = True
            if not (0.03    <= data_row['WallArea']               <= 135.15): exclude_row = True
            if not (-1.41   <= data_row['FloorArea']              <= 1596.88):exclude_row = True
            if not (14.73   <= data_row['GroundFloorArea(sq m)']  <= 143.84): exclude_row = True
            if not (-4.74   <= data_row['RoofArea']               <= 725.23): exclude_row = True
            if not (1.72    <= data_row['WindowArea']             <= 47.62 ): exclude_row = True
            if not (1.78    <= data_row['DoorArea']               <= 2.02  ): exclude_row = True

        case 'Ground-floor apartment':
            if not (3.72    <= data_row['LivingAreaPercent']      <= 64.30 ): exclude_row = True
            if not (-5.79   <= data_row['WallArea']               <= 113.86): exclude_row = True
            if not (2.23    <= data_row['FloorArea']              <= 107.71): exclude_row = True
            if not (14.74   <= data_row['GroundFloorArea(sq m)']  <= 125.67): exclude_row = True
            if not (-0.19   <= data_row['RoofArea']               <= 214.01): exclude_row = True
            if not (2.96    <= data_row['WindowArea']             <= 32.76 ): exclude_row = True
            if not (1.45    <= data_row['DoorArea']               <= 2.40  ): exclude_row = True

        case 'Mid-floor apartment':
            if not (21.59   <= data_row['LivingAreaPercent']      <= 65.04 ): exclude_row = True
            if not (-0.75   <= data_row['WallArea']               <= 104.89): exclude_row = True
            if not (0       <= data_row['FloorArea']              <= 0     ): exclude_row = True
            if not (8.61    <= data_row['GroundFloorArea(sq m)']  <= 114.22): exclude_row = True
            if not (0       <= data_row['RoofArea']               <= 0     ): exclude_row = True
            if not (2.77    <= data_row['WindowArea']             <= 41.77 ): exclude_row = True
            if not (0       <  data_row['DoorArea']               <= 1.91  ): exclude_row = True

        case 'Basement Dwellinge':
            if not (-4.70   <= data_row['LivingAreaPercent']      <= 81.83 ): exclude_row = True
            if not (0.94    <= data_row['WallArea']               <= 148.01): exclude_row = True
            if not (-12.76  <= data_row['FloorArea']              <= 141.22): exclude_row = True
            if not (2.43    <= data_row['GroundFloorArea(sq m)']  <= 189.37): exclude_row = True
            if not (-0.21   <= data_row['RoofArea']               <= 238.13): exclude_row = True
            if not (-0.28   <= data_row['WindowArea']             <= 32.29 ): exclude_row = True
            if not (0.29    <= data_row['DoorArea']               <= 2.23  ): exclude_row = True

    # Clauses 17, 18 - UValues per Thermal Era
    if(data_row['ThermalEra'] == 'Pre'):
        if not ((1.10 <= data_row['UvalueDoor']     <= 3.90) or data_row['UvalueDoor'] == 0):   exclude_row = True
        if not ((1.18 <= data_row['UValueWindow']   <= 5.70) or data_row['UValueWindow'] == 0): exclude_row = True
        if not ((0.13 <= data_row['UValueRoof']     <= 1.99) or data_row['UValueRoof'] == 0):   exclude_row = True
        if not ((0.16 <= data_row['UValueFloor']    <= 1.14) or data_row['UValueFloor'] == 0):  exclude_row = True
        if not  (0.20 <=    data_row['UValueWall']     <= 2.90):   exclude_row = True # not allowed to be zero
    elif(data_row['ThermalEra'] == 'Post'):
        if not ((0.83 <= data_row['UvalueDoor']     <= 3.54) or data_row['UvalueDoor'] == 0):   exclude_row = True
        if not ((0.77 <= data_row['UValueWindow']   <= 4.80) or data_row['UValueWindow'] == 0): exclude_row = True
        if not ((0.11 <= data_row['UValueRoof']     <= 0.68) or data_row['UValueRoof'] == 0):   exclude_row = True
        if not ((0.11 <= data_row['UValueFloor']    <= 1.14) or data_row['UValueFloor'] == 0):  exclude_row = True
        if not  (0.14 <= data_row['UValueWall']     <= 1.72):   exclude_row = True # not allowed to be zero


    # When all checks are complete, return the final decision
    return exclude_row





# Swapingg deterministic default value with more accurate defaults based on material reserach conducted 
# on the stadards and broadly known types used within the given age band
def find_and_replace(data_row: pd.Series) -> pd.Series:

    match data_row['AgeBand']:
        case 'A':
            if (data_row['UValueWall'] == 2.10) and (data_row['FirstWallType_Description'] == 'Unknown'):               data_row['UValueWall'] = 2.69
            if (data_row['UValueWall'] == 2.10) and (data_row['FirstWallType_Description'] == 'Stone'):                 data_row['UValueWall'] = 2.90
            if (data_row['UValueWall'] == 1.64) and (data_row['FirstWallType_Description'] == '325mm Solid Brick'):     data_row['UValueWall'] = 1.55
            if (data_row['UValueRoof'] == 2.30): data_row['UValueRoof'] = 0.71
        case 'B':
            if (data_row['UValueWall'] == 2.10) and (data_row['FirstWallType_Description'] == 'Unknown'):               data_row['UValueWall'] = 1.75
            if (data_row['UValueWall'] == 2.10) and (data_row['FirstWallType_Description'] == 'Stone'):                 data_row['UValueWall'] = 3.28
            if (data_row['UValueWall'] == 2.10) and (data_row['FirstWallType_Description'] == '225mm Solid brick'):     data_row['UValueWall'] = 1.75
            if (data_row['UValueWall'] == 1.64) and (data_row['FirstWallType_Description'] == '325mm Solid Brick'):     data_row['UValueWall'] = 1.55
            if (data_row['UValueRoof'] == 2.30): data_row['UValueRoof'] = 0.71
        case 'C': 
            if (data_row['UValueWall'] == 2.10) and (data_row['FirstWallType_Description'] == 'Unknown'):               data_row['UValueWall'] = 2.12
            if (data_row['UValueWall'] == 2.10) and (data_row['FirstWallType_Description'] == '225mm Solid brick'):     data_row['UValueWall'] = 1.75
            if (data_row['UValueWall'] == 1.78) and (data_row['FirstWallType_Description'] == '300mm Cavity'):          data_row['UValueWall'] = 1.20
            if (data_row['UValueWall'] == 2.20) and (data_row['FirstWallType_Description'] == 'Solid Mass Concrete'):   data_row['UValueWall'] = 2.12
            if (data_row['UValueRoof'] == 2.30): data_row['UValueRoof'] = 0.71
        case 'D': 
            if (data_row['UValueWall'] == 2.10) and (data_row['FirstWallType_Description'] == 'Unknown'):               data_row['UValueWall'] = 2.69
            if (data_row['UValueWall'] == 1.78) and (data_row['FirstWallType_Description'] == '300mm Cavity'):          data_row['UValueWall'] = 1.85
            if (data_row['UValueWall'] == 2.20) and (data_row['FirstWallType_Description'] == 'Solid Mass Concrete'):   data_row['UValueWall'] = 2.12
            if (data_row['UValueWall'] == 2.40) and (data_row['FirstWallType_Description'] == 'Concrete Hollow Block'): data_row['UValueWall'] = 2.69
            if (data_row['UValueRoof'] == 2.30): data_row['UValueRoof'] = 0.71
        case 'E': 
            if (data_row['UValueWall'] == 2.10) and (data_row['FirstWallType_Description'] == 'Unknown'):               data_row['UValueWall'] = 2.14
            if (data_row['UValueWall'] == 1.78) and (data_row['FirstWallType_Description'] == '300mm Cavity'):          data_row['UValueWall'] = 1.54
            if (data_row['UValueWall'] == 2.40) and (data_row['FirstWallType_Description'] == 'Concrete Hollow Block'): data_row['UValueWall'] = 2.14
            if (data_row['UValueRoof'] == 2.30): data_row['UValueRoof'] = 0.71
        case 'F': 
            if (data_row['UValueWall'] == 1.10) and (data_row['FirstWallType_Description'] == 'Unknown'):               data_row['UValueWall'] = 1.83
            if (data_row['UValueWall'] == 1.10) and (data_row['FirstWallType_Description'] == '300mm Cavity'):          data_row['UValueWall'] = 1.43
            if (data_row['UValueWall'] == 0.60) and (data_row['FirstWallType_Description'] == '300mm Filled Cavity'):   data_row['UValueWall'] = 0.54
            if (data_row['UValueWall'] == 1.10) and (data_row['FirstWallType_Description'] == 'Concrete Hollow Block'): data_row['UValueWall'] = 1.83
            if (data_row['UValueRoof'] == 0.49): data_row['UValueRoof'] = 0.43
        case 'G': 
            if (data_row['UValueWall'] == 0.60) and (data_row['FirstWallType_Description'] == 'Unknown'):               data_row['UValueWall'] = 1.35
            if (data_row['UValueWall'] == 0.60) and (data_row['FirstWallType_Description'] == '300mm Cavity'):          data_row['UValueWall'] = 1.35
            if (data_row['UValueWall'] == 0.60) and (data_row['FirstWallType_Description'] == '300mm Filled Cavity'):   data_row['UValueWall'] = 0.54
            if (data_row['UValueWall'] == 0.60) and (data_row['FirstWallType_Description'] == 'Concrete Hollow Block'): data_row['UValueWall'] = 1.72
            if (data_row['UValueRoof'] == 0.49): data_row['UValueRoof'] = 0.43
        case 'H': 
            if (data_row['UValueWall'] == 0.55) and (data_row['FirstWallType_Description'] == 'Unknown'):               data_row['UValueWall'] = 0.39
            if (data_row['UValueWall'] == 0.55) and (data_row['FirstWallType_Description'] == '300mm Filled Cavity'):   data_row['UValueWall'] = 0.39
            if (data_row['UValueWall'] == 0.55) and (data_row['FirstWallType_Description'] == 'Concrete Hollow Block'): data_row['UValueWall'] = 0.54
            if (data_row['UValueWall'] == 0.55) and (data_row['FirstWallType_Description'] == 'Timber Frame'):          data_row['UValueWall'] = 0.40
            if (data_row['UValueRoof'] == 0.40): data_row['UValueRoof'] = 0.28
        case 'I': 
            if (data_row['UValueWall'] == 0.55) and (data_row['FirstWallType_Description'] == 'Unknown'):               data_row['UValueWall'] = 0.28
            if (data_row['UValueWall'] == 0.55) and (data_row['FirstWallType_Description'] == '300mm Filled Cavity'):   data_row['UValueWall'] = 0.29
            if (data_row['UValueWall'] == 0.55) and (data_row['FirstWallType_Description'] == 'Timber Frame'):          data_row['UValueWall'] = 0.35
            if (data_row['UValueRoof'] == 0.36): data_row['UValueRoof'] = 0.28
        case 'J': 
            if (data_row['UValueWall'] == 0.37) and (data_row['FirstWallType_Description'] == 'Unknown'):               data_row['UValueWall'] = 0.27
            if (data_row['UValueWall'] == 0.37) and (data_row['FirstWallType_Description'] == '300mm Filled Cavity'):   data_row['UValueWall'] = 0.27
            if (data_row['UValueWall'] == 0.37) and (data_row['FirstWallType_Description'] == 'Timber Frame'):          data_row['UValueWall'] = 0.30
            if (data_row['UValueRoof'] == 0.25): data_row['UValueRoof'] = 0.21
        case 'K': 
            if (data_row['UValueWall'] == 0.27) and (data_row['FirstWallType_Description'] == 'Unknown'):               data_row['UValueWall'] = 0.27
            if (data_row['UValueWall'] == 0.27) and (data_row['FirstWallType_Description'] == '300mm Filled Cavity'):   data_row['UValueWall'] = 0.21
            if (data_row['UValueWall'] == 0.27) and (data_row['FirstWallType_Description'] == 'Timber Frame'):          data_row['UValueWall'] = 0.27
            if (data_row['UValueRoof'] == 0.25): data_row['UValueRoof'] = 0.21

    return data_row



# Lay out the step by stem methodology of cleaning/filtering data entries
def cleaning_methodology(data_row:pd.Series) -> pd.Series:
    data_row = drop_unwanted_columns(data_row)
    data_row = add_desired_columns(data_row)
    data_row = correct_column_data(data_row)
    data_row = find_and_replace(data_row)
    return data_row


def process_csv_file(input_csv_file:str, output_csv_file:str, chunk_size:int = 1000) -> None:
    """
    This function applies the complete cleaning process (filter rows, drop columns, add columns,
    and replacing defaults with more accurate defaults) to the input data set and stores the result
    in the output dataset. To accomodate for RAM capacity variation and file size, this process is
    carried out in chunks and the input and output must point to separate files

    Args:
        input_csv_file: string path to CSV file
        output_csv_file: sting path to CSV file
        chunk_size: specifies the number of chunk size per file read to be used. Default to 1000.

    Returns:
        None
    
    Raises:
        FileNotFoundError: if file read fails
        FileAccessError: if the input or output file extension is not '.csv' or are not separate files 
    """
    # error checking
    if not input_csv_file.endswith('.csv') or not output_csv_file.endswith('.csv'):
        raise FileAccessError("This function only accepts filetype '.csv'")
    
    if input_csv_file == output_csv_file:
        raise FileAccessError("Same input and output file given. Because file read occurs in chunks data may be lost mid processing. "+ 
                              "Use different input and output files.")
    
    # file processing
    first_write = True
    for chunk in pd.read_csv(input_csv_file, chunksize = chunk_size):
        # clean
        chunk = chunk.apply(cleaning_methodology, axis = 1)

        # filter
        chunk = chunk.filter(items = [id for id in chunk.index if filter_by_criteria(chunk.loc[id])], axis = 0)

        # write
        chunk.to_csv(output_csv_file, 
                     mode = 'w' if first_write else 'a', 
                     header = first_write,
                     index = False)
        if(first_write): first_write = False



def main():
    input_txt_file = './Data/BERPublicSearch_09022024/BERPublicsearch.txt'
    input_csv_file = './Data/BERPublicSearch_09022024/BERPublicsearch_Intermediary.csv'
    output_csv_file = './Data/BERPublicSearch_09022024/BERPublicsearch_cleaned.csv'

    convert_txt_to_csv(input_txt_file, input_csv_file)
    process_csv_file(input_csv_file, output_csv_file)


if __name__ == '__main__':
    main()
