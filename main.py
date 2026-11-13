from drafter import *
from dataclasses import dataclass, field
import re
from chempy import Substance, balance_stoichiometry

# -----------------------------------------
# SECOND DATACLASS: Reaction
# Represents one chemical reaction analysis
# -----------------------------------------

set_website_title("Chemical Assistant")
set_site_information(
    author="Shaun Donnally",
    description="Complete simple chemistry calculations.",
    sources="",
    planning=[],
    links=[]
)
hide_debug_information()
set_website_framed(False)

@dataclass
class Reaction:
    equation: str
    reactants: dict[str, float]
    limiting_reactant: str
    theoretical_yield: float
    actual_yield: float
    percent_yield: float
    remaining_masses: dict[str, float]
    enthalpy: float
    reaction_type: str


# -----------------------------------------
# MAIN DATACLASS: State
# Stores information across application routes
# -----------------------------------------

@dataclass
class State:
    reaction_history: list[Reaction] = field(default_factory=list)
    current_equation: str = ""
    reactant_masses: dict[str, float] = field(default_factory=dict)
    calculation_results: dict[str, float] = field(default_factory=dict)
    reaction_enthalpy: float = 0.0
    selected_product: str = ""
    actual_product_mass: float = 0.0
    save_to_history: bool = False
    reaction_family: str = ""
    limiting_reactant: str = ""
    remaining_masses: dict[str, float] = field(default_factory=dict)

def calculate_molecular_weight(formula: str) -> float:
    """
    Calculates the molecular weight of a chemical
    formula using ChemPy.
    """
    try:
        substance = Substance.from_formula(formula)
        return float(substance.mass)
    except Exception:
        raise ValueError(
            "Invalid or unsupported chemical formula: " + formula
        )
    
def balance_reaction(equation: str) -> str:
    """
    Uses ChemPy to balance a chemical equation
    containing reactants and products.
    """
    try:
        if "->" in equation:
            sides = equation.split("->")
        elif "→" in equation:
            sides = equation.split("→")
        else:
            raise ValueError("Please include an arrow (->).")

        if len(sides) != 2:
            raise ValueError("The equation must contain one arrow.")

        reactants = set(
            formula.strip() for formula in sides[0].split("+")
        )
        products = set(
            formula.strip() for formula in sides[1].split("+")
        )

        if "" in reactants or "" in products:
            raise ValueError("Please enter valid chemical formulas.")

        balanced_reactants, balanced_products = balance_stoichiometry(
            reactants, products
        )

        left_side = []
        right_side = []

        for formula, coefficient in balanced_reactants.items():
            if coefficient == 1:
                left_side.append(formula)
            else:
                left_side.append(str(coefficient) + " " + formula)

        for formula, coefficient in balanced_products.items():
            if coefficient == 1:
                right_side.append(formula)
            else:
                right_side.append(str(coefficient) + " " + formula)

        return " + ".join(left_side) + " -> " + " + ".join(right_side)

    except Exception as error:
        raise ValueError("Could not balance equation: " + str(error))


def calculate_stoichiometry(equation, reactant_masses,
                            actual_product_mass, product_formula):
    """
    Calculates limiting reactant, theoretical yield,
    percent yield, and remaining reactant masses.
    """

    # Separate the reactants and products.
    sides = equation.split("->")

    if len(sides) != 2:
        raise ValueError("Please enter a balanced equation.")

    reactants = sides[0].split("+")
    products = sides[1].split("+")

    # Read the coefficients from the balanced equation.
    reactant_coefficients = {}
    product_coefficients = {}

    for part in reactants:
        part = part.strip()
        pieces = part.split(maxsplit=1)

        if len(pieces) == 2 and pieces[0].isdigit():
            coefficient = int(pieces[0])
            formula = pieces[1]
        else:
            coefficient = 1
            formula = part

        reactant_coefficients[formula] = coefficient

    for part in products:
        part = part.strip()
        pieces = part.split(maxsplit=1)

        if len(pieces) == 2 and pieces[0].isdigit():
            coefficient = int(pieces[0])
            formula = pieces[1]
        else:
            coefficient = 1
            formula = part

        product_coefficients[formula] = coefficient

    if product_formula not in product_coefficients:
        raise ValueError("Product not found in equation.")

    if set(reactant_masses) != set(reactant_coefficients):
        raise ValueError("Reactant masses do not match the equation.")

    # Calculate available moles for each reactant.
    mole_ratios = {}

    for formula, mass in reactant_masses.items():
        if mass <= 0:
            raise ValueError("Reactant masses must be positive.")

        molar_mass = calculate_molecular_weight(formula)
        available_moles = mass / molar_mass

        ratio = available_moles / reactant_coefficients[formula]
        mole_ratios[formula] = ratio

    # The smallest ratio identifies the limiting reactant.
    limiting_reactant = min(mole_ratios, key=mole_ratios.get)

    reaction_extent = mole_ratios[limiting_reactant]

    # Calculate theoretical product mass.
    product_moles = (
        reaction_extent * product_coefficients[product_formula]
    )

    product_molar_mass = calculate_molecular_weight(product_formula)

    theoretical_yield = product_moles * product_molar_mass

    if theoretical_yield <= 0:
        raise ValueError("Theoretical yield must be positive.")

    if actual_product_mass < 0:
        raise ValueError("Actual product mass cannot be negative.")

    percent_yield = (
        actual_product_mass / theoretical_yield
    ) * 100

    # Calculate remaining mass of each reactant.
    remaining_masses = {}

    for formula, mass in reactant_masses.items():
        molar_mass = calculate_molecular_weight(formula)
        initial_moles = mass / molar_mass

        consumed_moles = (
            reaction_extent * reactant_coefficients[formula]
        )

        leftover_moles = max(0, initial_moles - consumed_moles)

        remaining_masses[formula] = leftover_moles * molar_mass

    return {
        "limiting_reactant": limiting_reactant,
        "theoretical_yield": theoretical_yield,
        "actual_yield": actual_product_mass,
        "percent_yield": percent_yield,
        "remaining_masses": remaining_masses
    }

# -----------------------------------------
# ROUTE 1: Homepage
# -----------------------------------------





@route
def index(state: State) -> Page:
    return Page(state, [
        # Main navy heading
        change_background_color(
            change_padding(
                change_text_align(
                    change_color(
                        Header("CHEMISTRY REACTION ASSISTANT"),
                        "#FFFFFF"
                    ),
                    "center"
                ),
                "20px"
            ),
            "#142B46"
        ),

        # Welcome section
        change_text_align(
            change_color(
                Header("Welcome to Your Chemistry Workspace"),
                "#087F8C"
            ),
            "center"
        ),

        change_text_align(
            Text(
                "Your workspace for chemical calculations, "
                "reaction analysis, and stoichiometry."
            ),
            "center"
        ),

        "\n",

        # Reaction tools
        change_background_color(
            change_padding(
                Header("REACTION TOOLS"),
                "15px"
            ),
            "#F1F5F9"
        ),
        Text("Analyze chemical reactions and balance equations."),
        Button("New Reaction Calculator", "new_reaction"),
        Button("Chemical Equation Balancer", "balance_equation"),

        "\n",

        # Calculation tools
        change_background_color(
            change_padding(
                Header("CALCULATION TOOLS"),
                "15px"
            ),
            "#F1F5F9"
        ),
        Text("Explore chemical properties and perform calculations."),
        Button("Molecular Weight Calculator", "molecular_weight"),

        "\n",

        # Saved work
        change_background_color(
            change_padding(
                Header("SAVED WORK"),
                "15px"
            ),
            "#F1F5F9"
        ),
        Text("Review your previous reaction calculations."),
        Button("Reaction History", "reaction_history"),

        "\n",

        # Learning resources
        change_background_color(
            change_padding(
                Header("LEARNING RESOURCES"),
                "15px"
            ),
            "#F1F5F9"
        ),
        Text("Explore helpful chemistry information."),
        Button("Chemistry Reference", "chemistry_reference"),

        "\n",

        # Footer
        change_text_align(
            change_color(
                Text("CHEMISTRY REACTION ASSISTANT | LEARNING TOOL"),
                "#087F8C"
            ),
            "center"
        )
    ])





# -----------------------------------------
# ROUTE 2: New Reaction
# -----------------------------------------


@route
def new_reaction(state: State) -> Page:
    return Page(state, [

        # Page heading
        change_background_color(
            change_padding(
                change_text_align(
                    change_color(
                        Header("NEW REACTION ANALYSIS"),
                        "#FFFFFF"
                    ),
                    "center"
                ),
                "20px"
            ),
            "#142B46"
        ),

        change_text_align(
            Text(
                "Enter your reaction information below "
                "to calculate its stoichiometry."
            ),
            "center"
        ),

        "\n",

        # Reaction equation
        change_background_color(
            change_padding(
                change_color(
                    Header("1. REACTION EQUATION"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text("Enter your chemical equation:"),
        TextBox(
            "equation",
            state.current_equation,
            placeholder="Example: 2 H2 + O2 -> 2 H2O"
        ),

        "\n",

        # Reactant information
        change_background_color(
            change_padding(
                change_color(
                    Header("2. REACTANT INFORMATION"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text("First reactant formula:"),
        TextBox("reactant1", "H2"),

        Text("First reactant mass (grams):"),
        TextBox("mass1", "4.00", kind="number"),

        "\n",

        Text("Second reactant formula:"),
        TextBox("reactant2", "O2"),

        Text("Second reactant mass (grams):"),
        TextBox("mass2", "32.00", kind="number"),

        "\n",

        # Product information
        change_background_color(
            change_padding(
                change_color(
                    Header("3. PRODUCT INFORMATION"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text("Desired product formula:"),
        TextBox("product", "H2O"),

        Text("Actual harvested product mass (grams):"),
        TextBox("actual_mass", "30.00", kind="number"),

        "\n",

        # Reaction energy
        change_background_color(
            change_padding(
                change_color(
                    Header("4. REACTION ENERGY"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text("Reaction enthalpy (kJ per reaction as written):"),
        TextBox("enthalpy", "-483.6", kind="number"),

        Text("Reaction family:"),
        SelectBox("reaction_family", [
            "Synthesis",
            "Decomposition",
            "Single Replacement",
            "Double Replacement",
            "Combustion",
            "Other"
        ]),

        "\n",

        # Save options
        change_background_color(
            change_padding(
                change_color(
                    Header("5. SAVE YOUR REACTION"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text("Save this reaction to your history?"),
        CheckBox("save_history", False),

        "\n\n",

        # Navigation
        Button("Submit Reaction", "calculate_reaction"),
        Button("Back to Home", "index")
    ])



# -----------------------------------------
# ROUTE 3: Calculate Reaction
# -----------------------------------------



@route
def calculate_reaction(state: State,
                       equation: str,
                       reactant1: str,
                       mass1: str,
                       reactant2: str,
                       mass2: str,
                       product: str,
                       actual_mass: str,
                       enthalpy: str,
                       reaction_family: str,
                       save_history: bool) -> Page:

    # Check that required text fields are not empty
    if (equation.strip() == "" or
        reactant1.strip() == "" or
        reactant2.strip() == "" or
        product.strip() == ""):

        return Page(state, [
            Header("Input Error"),
            "Please fill in all chemical formula fields.",
            Button("Return to Form", "new_reaction")
        ])

    # Convert numerical inputs
    try:
        mass1_value = float(mass1)
        mass2_value = float(mass2)
        actual_mass_value = float(actual_mass)
        enthalpy_value = float(enthalpy)

    except ValueError:
        return Page(state, [
            Header("Input Error"),
            "Please enter valid numerical values.",
            Button("Return to Form", "new_reaction")
        ])

    # Validate the masses
    if mass1_value <= 0 or mass2_value <= 0:
        return Page(state, [
            Header("Input Error"),
            "Reactant masses must be greater than zero.",
            Button("Return to Form", "new_reaction")
        ])

    if actual_mass_value < 0:
        return Page(state, [
            Header("Input Error"),
            "Actual product mass cannot be negative.",
            Button("Return to Form", "new_reaction")
        ])

    # Clean up the chemical formulas
    reactant1 = reactant1.strip()
    reactant2 = reactant2.strip()
    product = product.strip()

    if reactant1 == reactant2:
        return Page(state, [
            Header("Input Error"),
            "Please enter two different reactants.",
            Button("Return to Form", "new_reaction")
        ])

    try:
        # Balance the chemical equation
        balanced_equation = balance_reaction(equation)

        # Save the balanced equation and user inputs
        state.current_equation = balanced_equation
        state.reactant_masses = {
            reactant1: mass1_value,
            reactant2: mass2_value
        }
        state.selected_product = product
        state.actual_product_mass = actual_mass_value
        state.reaction_enthalpy = enthalpy_value
        state.reaction_family = reaction_family
        state.save_to_history = save_history

        # Calculate limiting reactant and product yield
        results = calculate_stoichiometry(
            balanced_equation,
            state.reactant_masses,
            actual_mass_value,
            product
        )

        # Save the calculation results
        state.limiting_reactant = results["limiting_reactant"]
        state.remaining_masses = results["remaining_masses"]

        state.calculation_results = {
            "theoretical_yield": results["theoretical_yield"],
            "actual_yield": results["actual_yield"],
            "percent_yield": results["percent_yield"]
        }

        # Determine the reaction type
        if enthalpy_value < 0:
            reaction_type = "Exothermic"
        elif enthalpy_value > 0:
            reaction_type = "Endothermic"
        else:
            reaction_type = "Thermoneutral"

        # Create a Reaction object for the history
        completed_reaction = Reaction(
            equation=balanced_equation,
            reactants=state.reactant_masses.copy(),
            limiting_reactant=results["limiting_reactant"],
            theoretical_yield=results["theoretical_yield"],
            actual_yield=results["actual_yield"],
            percent_yield=results["percent_yield"],
            remaining_masses=results["remaining_masses"],
            enthalpy=enthalpy_value,
            reaction_type=reaction_type
        )

        # Save the reaction if requested
        if save_history:
            state.reaction_history.append(completed_reaction)

        # Display the results
        return reaction_results(state)

    except (ValueError, KeyError, ZeroDivisionError) as error:
        return Page(state, [
            Header("Calculation Error"),
            str(error),
            "Please check your chemical equation and inputs.",
            Button("Try Again", "new_reaction"),
            Button("Back to Home", "index")
        ])



# -----------------------------------------
# ROUTE 4: Reaction Results
# -----------------------------------------



@route
def reaction_results(state: State) -> Page:
    return Page(state, [

        # Main page heading
        change_background_color(
            change_padding(
                change_text_align(
                    change_color(
                        Header("REACTION CALCULATION RESULTS"),
                        "#FFFFFF"
                    ),
                    "center"
                ),
                "20px"
            ),
            "#142B46"
        ),

        change_text_align(
            Text("Your reaction analysis is complete."),
            "center"
        ),

        "\n",

        # Balanced equation
        change_background_color(
            change_padding(
                change_color(
                    Header("BALANCED EQUATION"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        change_text_align(
            Text(state.current_equation),
            "center"
        ),

        "\n",

        # Limiting reactant
        change_background_color(
            change_padding(
                change_color(
                    Header("LIMITING REACTANT"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text(
            "The limiting reactant is: " +
            state.limiting_reactant
        ),

        "\n",

        # Product yield
        change_background_color(
            change_padding(
                change_color(
                    Header("PRODUCT YIELD"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text(
            "Theoretical Yield: " +
            str(round(
                state.calculation_results["theoretical_yield"], 3
            )) + " g"
        ),

        Text(
            "Actual Yield: " +
            str(round(
                state.calculation_results["actual_yield"], 3
            )) + " g"
        ),

        Text(
            "Percent Yield: " +
            str(round(
                state.calculation_results["percent_yield"], 2
            )) + "%"
        ),

        "\n",

        # Remaining reactants
        change_background_color(
            change_padding(
                change_color(
                    Header("REMAINING REACTANTS"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        "Remaining " + list(state.remaining_masses.keys())[0] +
        ": " + str(round(
            list(state.remaining_masses.values())[0], 3
        )) + " g",

        "Remaining " + list(state.remaining_masses.keys())[1] +
        ": " + str(round(
            list(state.remaining_masses.values())[1], 3
        )) + " g",

        "\n",

        # Reaction information
        change_background_color(
            change_padding(
                change_color(
                    Header("REACTION INFORMATION"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text(
            "Reaction Type: " +
            ("Exothermic" if state.reaction_enthalpy < 0
             else "Endothermic" if state.reaction_enthalpy > 0
             else "Thermoneutral")
        ),

        Text("Reaction Family: " + state.reaction_family),

        "\n",

        # Navigation
        Button("Calculate Another Reaction", "new_reaction"),
        Button("Back to Home", "index")
    ])




# -----------------------------------------
# ROUTE 5: Reaction History
# -----------------------------------------



@route
def reaction_history(state: State) -> Page:
    content = [

        # Main page heading
        change_background_color(
            change_padding(
                change_text_align(
                    change_color(
                        Header("REACTION HISTORY"),
                        "#FFFFFF"
                    ),
                    "center"
                ),
                "20px"
            ),
            "#142B46"
        ),

        change_text_align(
            Text("Review your previously saved reaction analyses."),
            "center"
        ),

        "\n"
    ]

    if len(state.reaction_history) == 0:
        content.append(
            change_background_color(
                change_padding(
                    Text("You have not saved any reactions yet."),
                    "15px"
                ),
                "#F1F5F9"
            )
        )

    else:
        for index, reaction in enumerate(state.reaction_history):

            # Individual saved reaction
            content.append(
                change_background_color(
                    change_padding(
                        change_color(
                            Header("SAVED REACTION " + str(index + 1)),
                            "#087F8C"
                        ),
                        "12px"
                    ),
                    "#F1F5F9"
                )
            )

            content.append(
                Text("Equation: " + reaction.equation)
            )

            content.append(
                Text(
                    "Limiting Reactant: " +
                    reaction.limiting_reactant
                )
            )

            content.append(
                Text(
                    "Percent Yield: " +
                    str(round(reaction.percent_yield, 2)) + "%"
                )
            )

            content.append(
                Button(
                    "View Reaction Details",
                    "reaction_details",
                    arguments={"index": index}
                )
            )

            content.append("\n")

    # Navigation and history controls
    content.append(
        change_background_color(
            change_padding(
                change_color(
                    Header("HISTORY OPTIONS"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        )
    )

    content.append(Button("Clear History", "clear_history"))
    content.append(Button("Back to Home", "index"))

    return Page(state, content)



# -----------------------------------------
# ROUTE 6: Reaction Details
# -----------------------------------------



@route
def reaction_details(state: State, index: int) -> Page:

    # Check that the selected reaction exists
    if index < 0 or index >= len(state.reaction_history):
        return Page(state, [

            change_background_color(
                change_padding(
                    change_text_align(
                        change_color(
                            Header("REACTION NOT FOUND"),
                            "#FFFFFF"
                        ),
                        "center"
                    ),
                    "20px"
                ),
                "#142B46"
            ),

            Text("This saved reaction could not be found."),
            Button("Back to History", "reaction_history")
        ])

    reaction = state.reaction_history[index]

    content = [

        # Main page heading
        change_background_color(
            change_padding(
                change_text_align(
                    change_color(
                        Header("REACTION DETAILS"),
                        "#FFFFFF"
                    ),
                    "center"
                ),
                "20px"
            ),
            "#142B46"
        ),

        Text("Detailed information about your saved reaction."),

        "\n",

        # Balanced equation
        change_background_color(
            change_padding(
                change_color(
                    Header("BALANCED EQUATION"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text(reaction.equation),

        "\n",

        # Reactant masses
        change_background_color(
            change_padding(
                change_color(
                    Header("REACTANT MASSES"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        )
    ]

    for formula, mass in reaction.reactants.items():
        content.append(
            Text(formula + ": " + str(round(mass, 3)) + " g")
        )

    # Calculation results
    content.append("\n")

    content.append(
        change_background_color(
            change_padding(
                change_color(
                    Header("CALCULATION RESULTS"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        )
    )

    content.append(
        Text("Limiting Reactant: " + reaction.limiting_reactant)
    )

    content.append(
        Text(
            "Theoretical Yield: " +
            str(round(reaction.theoretical_yield, 3)) + " g"
        )
    )

    content.append(
        Text(
            "Actual Yield: " +
            str(round(reaction.actual_yield, 3)) + " g"
        )
    )

    content.append(
        Text(
            "Percent Yield: " +
            str(round(reaction.percent_yield, 2)) + "%"
        )
    )

    # Remaining reactants
    content.append("\n")

    content.append(
        change_background_color(
            change_padding(
                change_color(
                    Header("REMAINING REACTANTS"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        )
    )

    for formula, mass in reaction.remaining_masses.items():
        content.append(
            Text(formula + ": " + str(round(mass, 3)) + " g")
        )

    # Reaction information
    content.append("\n")

    content.append(
        change_background_color(
            change_padding(
                change_color(
                    Header("REACTION INFORMATION"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        )
    )

    content.append(
        Text("Enthalpy: " + str(reaction.enthalpy) + " kJ")
    )

    content.append(
        Text("Reaction Type: " + reaction.reaction_type)
    )

    # Navigation
    content.append("\n")
    content.append(Button("Back to History", "reaction_history"))
    content.append(Button("Back to Home", "index"))

    return Page(state, content)



# -----------------------------------------
# ROUTE 7: Molecular Weight Calculator
# -----------------------------------------


@route
def molecular_weight(state: State) -> Page:
    return Page(state, [

        # Main page heading
        change_background_color(
            change_padding(
                change_text_align(
                    change_color(
                        Header("MOLECULAR WEIGHT CALCULATOR"),
                        "#FFFFFF"
                    ),
                    "center"
                ),
                "20px"
            ),
            "#142B46"
        ),

        change_text_align(
            Text(
                "Calculate the molecular weight of a chemical "
                "compound using its chemical formula."
            ),
            "center"
        ),

        "\n",

        # Formula input section
        change_background_color(
            change_padding(
                change_color(
                    Header("CHEMICAL FORMULA"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text("Enter a chemical formula below:"),

        TextBox(
            "formula",
            "H2O",
            placeholder="Example: H2O, CO2, C6H12O6"
        ),

        "\n",

        # Instructions
        change_background_color(
            change_padding(
                Text(
                    "Enter the chemical formula using element "
                    "symbols and subscripts as numbers. "
                    "For example, enter H2O for water."
                ),
                "15px"
            ),
            "#F1F5F9"
        ),

        "\n",

        # Navigation and calculation
        Button(
            "Calculate Molecular Weight",
            "show_molecular_weight"
        ),

        Button("Back to Home", "index")
    ])


@route
def show_molecular_weight(state: State, formula: str) -> Page:
    try:
        mass = calculate_molecular_weight(formula)

        return Page(state, [
            Header("Molecular Weight Result"),
            "Chemical Formula: " + formula,
            "Molecular Weight: " +
            str(round(mass, 3)) + " g/mol",
            Button("Calculate Another", "molecular_weight"),
            Button("Back to Home", "index")
        ])

    except ValueError as error:
        return Page(state, [
            Header("Invalid Formula"),
            str(error),
            Button("Try Again", "molecular_weight"),
            Button("Back to Home", "index")
        ])


# -----------------------------------------
# ROUTE 8: Chemistry Reference
# -----------------------------------------


@route
def chemistry_reference(state: State) -> Page:
    return Page(state, [

        # Main page heading
        change_background_color(
            change_padding(
                change_text_align(
                    change_color(
                        Header("CHEMISTRY REFERENCE"),
                        "#FFFFFF"
                    ),
                    "center"
                ),
                "20px"
            ),
            "#142B46"
        ),

        change_text_align(
            Text(
                "Explore important chemistry concepts "
                "and reaction calculations."
            ),
            "center"
        ),

        "\n",

        # Stoichiometry
        change_background_color(
            change_padding(
                change_color(
                    Header("STOICHIOMETRY"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text(
            "Stoichiometry is the study of the quantitative "
            "relationships between reactants and products "
            "in a chemical reaction."
        ),

        "\n",

        # Limiting reactants
        change_background_color(
            change_padding(
                change_color(
                    Header("LIMITING REACTANTS"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text(
            "The limiting reactant is the reactant that is "
            "used up first. It determines the maximum amount "
            "of product that can form."
        ),

        "\n",

        # Theoretical yield
        change_background_color(
            change_padding(
                change_color(
                    Header("THEORETICAL YIELD"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text(
            "Theoretical yield is the maximum amount of "
            "product that can be produced based on the "
            "available reactants."
        ),

        "\n",

        # Percent yield
        change_background_color(
            change_padding(
                change_color(
                    Header("PERCENT YIELD"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text(
            "Percent yield compares the actual amount of "
            "product collected with the theoretical yield."
        ),

        Text(
            "Percent Yield = (Actual Yield / Theoretical Yield) "
            "* 100"
        ),

        "\n",

        # Exothermic and endothermic reactions
        change_background_color(
            change_padding(
                change_color(
                    Header("EXOTHERMIC AND ENDOTHERMIC REACTIONS"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text(
            "Exothermic reactions release heat to their "
            "surroundings. Their enthalpy change is negative."
        ),

        Text(
            "Endothermic reactions absorb heat from their "
            "surroundings. Their enthalpy change is positive."
        ),

        "\n",

        # Navigation
        Button("Back to Home", "index")
    ])



# -----------------------------------------
# ROUTE 9: Clear History
# -----------------------------------------

@route
def clear_history(state: State) -> Page:
    state.reaction_history.clear()

    return Page(state, [
        "REACTION HISTORY CLEARED",
        "\n\n",
        "Your saved reaction analyses have been cleared.",
        "\n\n",
        Button("View History", "reaction_history"),
        Button("Back to Home", "index")
    ])


@route
def balance_equation(state: State) -> Page:
    return Page(state, [

        # Main page heading
        change_background_color(
            change_padding(
                change_text_align(
                    change_color(
                        Header("CHEMICAL EQUATION BALANCER"),
                        "#FFFFFF"
                    ),
                    "center"
                ),
                "20px"
            ),
            "#142B46"
        ),

        change_text_align(
            Text(
                "Balance chemical equations by determining "
                "the correct coefficients for each compound."
            ),
            "center"
        ),

        "\n",

        # Equation input section
        change_background_color(
            change_padding(
                change_color(
                    Header("CHEMICAL EQUATION"),
                    "#087F8C"
                ),
                "12px"
            ),
            "#F1F5F9"
        ),

        Text("Enter an unbalanced chemical equation:"),

        TextBox(
            "equation",
            "H2 + O2 -> H2O",
            placeholder="Example: H2 + O2 -> H2O"
        ),

        "\n",

        # Instructions
        change_background_color(
            change_padding(
                Text(
                    "Use + signs between compounds and an arrow "
                    "(->) between reactants and products. "
                    "Enter chemical formulas without coefficients."
                ),
                "15px"
            ),
            "#F1F5F9"
        ),

        "\n",

        # Navigation and balancing
        Button("Balance Equation", "show_balanced_equation"),

        Button("Back to Home", "index")
    ])



@route
def show_balanced_equation(state: State, equation: str) -> Page:
    try:
        balanced = balance_reaction(equation)

        state.current_equation = balanced

        return Page(state, [

            # Main page heading
            change_background_color(
                change_padding(
                    change_text_align(
                        change_color(
                            Header("EQUATION BALANCED SUCCESSFULLY"),
                            "#FFFFFF"
                        ),
                        "center"
                    ),
                    "20px"
                ),
                "#142B46"
            ),

            change_text_align(
                Text("Your chemical equation has been balanced."),
                "center"
            ),

            "\n",

            # Balanced equation section
            change_background_color(
                change_padding(
                    change_color(
                        Header("BALANCED EQUATION"),
                        "#087F8C"
                    ),
                    "12px"
                ),
                "#F1F5F9"
            ),

            change_text_align(
                Text(balanced),
                "center"
            ),

            "\n",

            # Navigation
            Button("Balance Another Equation", "balance_equation"),
            Button("Back to Home", "index")
        ])

    except ValueError as error:
        return Page(state, [

            # Error page heading
            change_background_color(
                change_padding(
                    change_text_align(
                        change_color(
                            Header("BALANCING ERROR"),
                            "#FFFFFF"
                        ),
                        "center"
                    ),
                    "20px"
                ),
                "#142B46"
            ),

            "\n",

            # Error message
            change_background_color(
                change_padding(
                    Text(str(error)),
                    "15px"
                ),
                "#F1F5F9"
            ),

            "\n",

            # Navigation
            Button("Try Again", "balance_equation"),
            Button("Back to Home", "index")
        ])

# -----------------------------------------
# START THE APPLICATION
# -----------------------------------------

start_server(State(), project_packages=["chempy"])
