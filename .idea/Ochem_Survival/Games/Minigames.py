import random as rd
import sqlite3 as sql
from io import BytesIO
from PIL import Image

def Most_Acidic():
    ochem_database = sql.connect('ochem.db')
    cursor = ochem_database.cursor()

    cursor.execute("SELECT MIN(id), MAX(id) FROM ochem_table;")
    min_id, max_id = cursor.fetchone()

    # Step 2: Generate 4 unique random numbers within the ID range
    random_compounds = rd.sample(range(min_id, max_id + 1), 4)

    extract_query = """
        SELECT DISTINCT pH, chemical_formula, iupac, image_file FROM ochem_table
        WHERE id IN (?,?,?,?);
        """

    cursor.execute(extract_query, random_compounds)
    my_compounds = cursor.fetchall()

    ochem_database.commit()
    ochem_database.close()

    Correct_compound = my_compounds[0]
    Wrong_compound1 = my_compounds[1]
    Wrong_compound2 = my_compounds[2]
    Wrong_compound3 = my_compounds[3]

    Correct_image = Image.open(BytesIO(Correct_compound[3]))
    Wrong_image1 = Image.open(BytesIO(Wrong_compound1[3]))
    Wrong_image2 = Image.open(BytesIO(Wrong_compound2[3]))
    Wrong_image3 = Image.open(BytesIO(Wrong_compound3[3]))

    Correct_image.show()
    Wrong_image1.show()
    Wrong_image2.show()
    Wrong_image3.show()
def Structure_To_Name():
    ochem_database = sql.connect("Ochem.db")
    cursor = ochem_database.cursor()

    extract_query = """
    SELECT image_file, iupac FROM ochem_table
    where id in (?,?,?,?)"""

    cursor.execute("SELECT MIN(id), MAX(id) from ochem_table;")
    min_id, max_id = cursor.fetchone()
    random_compounds = rd.sample(range(min_id, max_id), 4)

    cursor.execute(extract_query, random_compounds)
    my_compounds = cursor.fetchall()

    ochem_database.commit()
    ochem_database.close()

    Correct_compound = my_compounds[0]
    Wrong_compound1 = my_compounds[1]
    Wrong_compound2 = my_compounds[2]
    Wrong_compound3 = my_compounds[3]

    Correct_Name = Correct_compound[1]
    Wrong_Name1 = Wrong_compound1[1]
    Wrong_Name2 = Wrong_compound2[1]
    Wrong_Name3 = Wrong_compound3[1]

    Display_Image = Image.open(BytesIO(Correct_compound[0]))

def Name_To_Structure():
    ochem_database = sql.connect('Ochem.db')

    cursor = ochem_database.cursor()
    cursor.execute("SELECT MIN(id), MAX(id) from ochem_table;")
    min_id, max_id = cursor.fetchone()

    random_compounds = rd.sample(range(min_id, max_id + 1), 4)

    extract_query = """
    SELECT image_file, iupac FROM ochem_table
    WHERE id IN (?,?,?,?)"""

    cursor.execute(extract_query, random_compounds)
    my_compounds = cursor.fetchall()

    ochem_database.commit()
    ochem_database.close()

    Correct_compound = my_compounds[0]
    Wrong_compound1 = my_compounds[1]
    Wrong_compound2 = my_compounds[2]
    Wrong_compound3 = my_compounds[3]

    Correct_Image = Image.open(BytesIO(Correct_compound[0]))
    Wrong_Image1 = Image.open(BytesIO(Wrong_compound1[0]))
    Wrong_Image2 = Image.open(BytesIO(Wrong_compound2[0]))
    Wrong_Image3 = Image.open(BytesIO(Wrong_compound3[0]))

    Display_text = Correct_compound[1]
    print(Display_text)
