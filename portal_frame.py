from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.gp import gp_Vec, gp_Trsf, gp_Ax1, gp_Dir, gp_Pnt
from OCC.Display.SimpleGui import init_display
from draw_i_section import create_i_section
from draw_rectangular_prism import create_rectangular_prism
import math

def create_custom_structure(
    column_height, column_thickness, rafter_length, rafter_angle, 
    roof_length, roof_width, roof_height, flange_thickness, web_thickness,
    prism_spacing
):
    """
    Create a CAD model of the described structure with prisms placed uniformly along the rafters to form the roof.

    Parameters:
    - column_height: Height of the columns
    - column_thickness: Thickness of the I-section columns
    - rafter_length: Length of the rafters
    - rafter_angle: Angle of inclination of the rafters (in degrees)
    - roof_length: Length of the rectangular roof prism
    - roof_width: Width of the rectangular roof prism
    - roof_height: Height of the rectangular roof prism
    - flange_thickness: Thickness of the I-section flanges
    - web_thickness: Thickness of the I-section web
    - prism_spacing: Horizontal distance between each roof prism along the rafter

    Returns:
    - structure: The complete structure as a TopoDS_Shape
    """
    # Convert angle from degrees to radians
    angle_rad = math.radians(rafter_angle)

    # Distance between opposite vertical columns
    column_spacing_x = 2 * rafter_length * math.cos(angle_rad)

    # Create vertical I-section columns
     # Create vertical I-section columns (passing column_height as first parameter)
    column = create_i_section(column_height, column_thickness, column_thickness, flange_thickness, web_thickness)

    # Rotate to make it vertical
    trsf = gp_Trsf()
    trsf.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)), -math.pi / 2)  # Rotate 90° around Y-axis
    column = BRepBuilderAPI_Transform(column, trsf, True).Shape()
    columns = []

    # Position columns
    num_columns = 5
    column_spacing_y = rafter_length
    for i in range(num_columns):
        # Left row
        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(0, i * column_spacing_y, 0))
        left_column = BRepBuilderAPI_Transform(column, trsf, True).Shape()
        columns.append(left_column)

        # Right row
        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(column_spacing_x+column_thickness, i * column_spacing_y, 0))
        right_column = BRepBuilderAPI_Transform(column, trsf, True).Shape()
        columns.append(right_column)

    # Fuse columns into a single shape
    structure = columns[0]
    for col in columns[1:]:
        structure = BRepAlgoAPI_Fuse(structure, col).Shape()

    box = BRepPrimAPI_MakeBox(1000, 1000, 1000).Shape()  # Create a box of size 1000x1000x100
    for i in range(num_columns):
        # Left column base position
        column_base_left = gp_Vec(-column_thickness*2, i * column_spacing_y-column_thickness*1.5, 0)
        trsf_left = gp_Trsf()
        trsf_left.SetTranslation(column_base_left)
        box_left = BRepBuilderAPI_Transform(box, trsf_left, True).Shape()
        
        # Right column base position
        column_base_right = gp_Vec(column_spacing_x-column_thickness*2, i * column_spacing_y-column_thickness*1.5, 0)
        trsf_right = gp_Trsf()
        trsf_right.SetTranslation(column_base_right)
        box_right = BRepBuilderAPI_Transform(box, trsf_right, True).Shape()

        # Fuse the boxes into the structure
        structure = BRepAlgoAPI_Fuse(structure, box_left).Shape()
        structure = BRepAlgoAPI_Fuse(structure, box_right).Shape()

    # Create inclined rafters for each column
    rafter = create_i_section(rafter_length, column_thickness, column_thickness, flange_thickness, web_thickness)

    for i in range(num_columns):
        # Get column tops for left and right sides
        left_column_top = gp_Pnt(0, i * column_spacing_y, column_height)
        right_column_top = gp_Pnt(0, i * column_spacing_y, column_height)

        # Apex of the rafters (the center point above the two columns)
        apex = gp_Pnt(column_spacing_x / 2, i * column_spacing_y, column_height + math.tan(angle_rad) * (column_spacing_x / 2))

        # Left rafter for the current frame (connects left column to apex)
        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(0, i * column_spacing_y, column_height))  # Position at left column
        rafter_left = BRepBuilderAPI_Transform(rafter, trsf, True).Shape()

        # Right rafter for the current frame (connects right column to apex)
        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(column_spacing_x, i * column_spacing_y, column_height))  # Position at right column
        rafter_right = BRepBuilderAPI_Transform(rafter, trsf, True).Shape()

        # Adjust the rafter to the apex, and change its orientation accordingly
        trsf_left = gp_Trsf()
        trsf_left.SetTranslation(gp_Vec(0, i * column_spacing_y, column_height))  # Left rafter base at the left column
        trsf_left.SetRotation(gp_Ax1(gp_Pnt(0, i * column_spacing_y, column_height), gp_Dir(0, 1, 0)), -angle_rad)  # Rotate to desired angle
        rafter_left = BRepBuilderAPI_Transform(rafter_left, trsf_left, True).Shape()

        trsf_right = gp_Trsf()
        adjust=20
        trsf_right.SetTranslation(gp_Vec(column_spacing_x, i * column_spacing_y, column_height))  # Right rafter base at the right column
        trsf_right.SetRotation(gp_Ax1(gp_Pnt(column_spacing_x+adjust, i * column_spacing_y, column_height+column_thickness/2.1), gp_Dir(0, 1, 0)), angle_rad-math.pi)  # Rotate to desired angle
        rafter_right = BRepBuilderAPI_Transform(rafter_right, trsf_right, True).Shape()

        # Fuse the rafters into the structure
        structure = BRepAlgoAPI_Fuse(structure, rafter_left).Shape()
        structure = BRepAlgoAPI_Fuse(structure, rafter_right).Shape()

    # Left Rafter
    num_prisms = desired_number_of_prisms  # Set the desired number of prisms
    prism_spacing = rafter_length * math.cos(angle_rad) / (num_prisms - 1)  # Divide the rafter length by the gaps (num_prisms - 1)

    for i in range(num_prisms):
        if (i==num_prisms-1):
        # Calculate the position along the rafter (X and Z coordinates)
            x_position_left = i * prism_spacing+roof_width/2  # Along the rafter length (X-axis) for the left rafter
            z_position_left = column_height + roof_height + math.tan(angle_rad) * x_position_left -column_thickness/2# Adjusted Z-position along the slope for the left rafter
        else:
            x_position_left = i * prism_spacing  # Along the rafter length (X-axis) for the left rafter
            z_position_left = column_height + roof_height + math.tan(angle_rad) * x_position_left +flange_thickness*3.5 # Adjusted Z-position along the slope for the left rafter

        # Create a roof prism
        roof_left = create_rectangular_prism(roof_length, roof_width, roof_height)

        # Translation to the position along the left rafter
        translation_left = gp_Trsf()
        translation_left.SetTranslation(gp_Vec(x_position_left, 0, z_position_left))  # Move to the left rafter position
        roof_left = BRepBuilderAPI_Transform(roof_left, translation_left, True).Shape()

        # Rotation to make the prism perpendicular to the left rafter
        rotation_axis_left = gp_Ax1(gp_Pnt(x_position_left, 0, z_position_left), gp_Dir(math.sin(0), 0, math.cos(0)))
        rotation_left = gp_Trsf()
        rotation_left.SetRotation(rotation_axis_left, math.pi / 2)  # Rotate 90 degrees to make it perpendicular
        roof_left = BRepBuilderAPI_Transform(roof_left, rotation_left, True).Shape()

        # Fuse the prism into the left rafter structure
        structure = BRepAlgoAPI_Fuse(structure, roof_left).Shape()

    # Right Rafter
    for i in range(num_prisms-1):
        # Calculate the position along the rafter (X and Z coordinates)
        x_position_right = column_spacing_x - i * prism_spacing 
        x_position = -i * prism_spacing  # Along the rafter length (X-axis) for the right rafter (negative direction)
        z_position_right = column_height + math.tan(angle_rad) * abs(x_position) + column_thickness*1.45 # Adjusted Z-position along the slope for the right rafter

        # Create a roof prism
        roof_right = create_rectangular_prism(roof_length, roof_width, roof_height)

        # Translation to the position along the right rafter
        translation_right = gp_Trsf()
        translation_right.SetTranslation(gp_Vec(x_position_right, 0, z_position_right))  # Move to the right rafter position
        roof_right = BRepBuilderAPI_Transform(roof_right, translation_right, True).Shape()

        # Rotation to make the prism perpendicular to the right rafter
        rotation_axis_right = gp_Ax1(gp_Pnt(x_position_right, 0, z_position_right), gp_Dir(math.sin(0), 0, math.cos(0)))
        rotation_right = gp_Trsf()
        rotation_right.SetRotation(rotation_axis_right, math.pi / 2)  # Rotate 90 degrees to make it perpendicular
        roof_right = BRepBuilderAPI_Transform(roof_right, rotation_right, True).Shape()

        # Fuse the prism into the right rafter structure
        structure = BRepAlgoAPI_Fuse(structure, roof_right).Shape()

    return structure


if __name__ == "__main__":
    # Define dimensions
    column_height = 4000.0
    column_thickness = 250.0#please don't change this value as many calculation done on this basis
    rafter_length = 9000.0
    rafter_angle = float(input("Enter the angle of inclination:\n"))
    roof_length = rafter_length * 4 + 200
    roof_width = 200.0
    roof_height = 200.0
    flange_thickness = 20
    web_thickness = 9.10
    desired_number_of_prisms = int(input("Enter the number of prisms:\n"))
    prism_spacing = rafter_length / (desired_number_of_prisms - 1)

    # Create the structure
    custom_structure = create_custom_structure(
        column_height, column_thickness, rafter_length, rafter_angle,
        roof_length, roof_width, roof_height, flange_thickness, web_thickness, prism_spacing
    )

    # Visualization
    display, start_display, add_menu, add_function_to_menu = init_display()
    display.DisplayShape(custom_structure, update=True)
    display.FitAll()
    start_display()
