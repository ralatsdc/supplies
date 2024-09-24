from argparse import ArgumentParser
import os
from subprocess import run

import pandas as pd

n_outer_rows = 3
n_outer_cols = 4

inner_cols = ["qty", "unt", "item"]
inner_algn = " c c l "


def begin_document(fp):
    """Begin LaTeX document.

    Parameters
    ----------
    fp : _io.TextIOWrapper
        File pointer

    Returns
    -------
    None
    """
    fp.write(r"\documentclass{article}" + "\n")
    fp.write(r"\usepackage{array}" + "\n")
    fp.write(r"\usepackage{geometry}" + "\n")
    fp.write(r"\geometry{letterpaper, landscape, margin=0.25in}" + "\n")
    fp.write(r"\begin{document}" + "\n")


def end_document(fp):
    """End LaTeX document.

    Parameters
    ----------
    fp : _io.TextIOWrapper
        File pointer

    Returns
    -------
    None
    """
    fp.write(r"\end{document}" + "\n")


def escape_specials(values):
    """Escape LaTeX special characters.

    Parameters
    ----------
    values : str or list(str)
        The values containing special characters to escape

    Returns
    -------
    str or list(str)
        The values containing escaped special characters
    """
    if len(values) == 1:
        return str(values[0]).replace("%", r"\%").replace("&", r"\&")
    else:
        return [str(value).replace("%", r"\%").replace("&", r"\&") for value in values]


def write_outer_cell(fp, group, n_inner_rows, name=None, write_rule=False):
    """Write the specified number of rows from the group to create the
    single column inner table and fill one cell of an outer table. The
    group is expected to contain items in a location sorted by order,
    or in a store department sorted alphabetically.

    Parameters
    ----------
    fp : _io.TextIOWrapper
        File pointer
    group : pd.DataFrame
        Pandas DataFrame containing items to write
    n_inner_rows : int
        Number of rows in the inner table
    name : None or str
        Name of the group location or department
    write_rule : boolean
        Flag to write rule, or not

    Returns
    -------
    pd.DataFrame
        Pandas DataFrame containing items that were not written
    """
    # Begin tabular environment
    fp.write(r"    \begin{tabular}[t]{" + inner_algn + "}\n")
    fp.write(r"    \\" + "\n")

    # Write the name of the group location or department, if needed
    if name:
        fp.write(
            r"    \multicolumn{"
            + str(len(inner_cols))
            + r"}{l}{\textbf{"
            + escape_specials([name])
            + r"}} \\"
            + "\n"
        )
        fp.write(r"    \hline" + "\n")
        fp.write(r"    \\" + "\n")
        n_inner_rows -= 2

    # Write the specified number of items
    n_inner_row = 0
    indexes = []
    for index, row in group.iterrows():
        if write_rule:
            # Write the rule, noting that the rule counts as one of the rows
            fp.write(
                r"    \rule[0pt]{0.25in}{0.5pt} &"
                + " & ".join(escape_specials(row[inner_cols[1:]].values))
            )

        else:
            # Write an item quantity, unit, and name
            fp.write("      " + " & ".join(escape_specials(row[inner_cols].values)))
        n_inner_row += 1
        indexes.append(index)

        if n_inner_row < n_inner_rows and n_inner_row < group.shape[0]:
            # Terminate a row if it is not the last row in the table or last item in the group
            fp.write(r" \\" + "\n")

        else:
            # Wrote the specified number or rows, or all items in the group
            break

    # End tabular environment
    fp.write("\n" + r"    \end{tabular}" + "\n")

    # Return the group with all written itmes dropped
    return group.drop(index=indexes)


def write_group_by(fp, group_by_label, group_names, n_inner_rows, write_rule=False):
    """Write the specified number of outer table rows and columns
    until all items in every group have been written. Groups contain
    all items in every location, or every store department. Writes the
    location or department name when starting to write items from the
    corresponding group.

    Parameters
    ----------
    fp : _io.TextIOWrapper
        File pointer
    group_by_label = pandas.api.typing.DataFrameGroupBy
        A groupby object that contains information about the groups
    n_inner_rows : int
        Number of rows in the inner table
    write_rule : boolean
        Flag to write rule, or not

    Returns
    -------
    None
    """
    # Begin tabular environment
    fp.write(r"  \begin{tabular}[t]{" + " p{2.5in} " * n_outer_cols + "}\n")

    # Write the specified number of outer table rows and columns until
    # all items in every group have been written.
    n_outer_row = 0
    n_outer_col = 0
    current_group_name = ""
    for name in group_names:
        group = group_by_label.get_group(name)

        # Write the group until it is consumed
        while group.shape[0] > 0:

            # Write group items
            if name == current_group_name:
                # Write group name when first encountered
                group = write_outer_cell(fp, group, n_inner_rows, write_rule=write_rule)

            else:
                current_group_name = name
                group = write_outer_cell(
                    fp,
                    group,
                    n_inner_rows,
                    name=current_group_name,
                    write_rule=write_rule,
                )

            # Count columns and check
            n_outer_col += 1
            if n_outer_col < n_outer_cols:
                if group.shape[0] > 0 or name != group_names[-1]:
                    # Separate cells if more items in the current
                    # group, or in another group need to be written
                    fp.write("    &\n")

            else:

                # Count rows and check
                n_outer_row += 1
                if n_outer_row < n_outer_rows:
                    # Terminate row if not the last
                    fp.write(r"  \\" + "\n")
                    fp.write(r"  \\" + "\n")

                    # Reinitialize number of columns
                    n_outer_col = 0

            # Check number of rows and columns
            if n_outer_row == n_outer_rows and n_outer_col == n_outer_cols:

                # End tabular environment since the specified number
                # of rows and columns have been written
                fp.write(r"  \end{tabular}" + "\n")

                # Reinitialize number of rows and columns
                n_outer_row = 0
                n_outer_col = 0

                # Begin tablular environment if more items in the
                # current group, or in another group need to be
                # written
                if group.shape[0] > 0 or name != group_names[-1]:
                    fp.write(
                        r"  \begin{tabular}[t]{" + " p{2.5in} " * n_outer_cols + "}\n"
                    )

            elif group.shape[0] == 0 and name == group_names[-1]:

                # End tabular environment since no more items need to
                # be written
                fp.write(r"  \end{tabular}" + "\n")


def main():
    """Provide a command line interface to typesetting supply
    inventories and corresponding shoping lists.
    """
    parser = ArgumentParser(
        description="Typeset supplies and corresponding shopping lists"
    )
    parser.add_argument(
        "-i",
        "--inventory-filename",
        default="../resources/inventory-2024-09-24.csv",
        help="the inventory filename",
    )
    args = parser.parse_args()

    # Read the inventory file
    inventory = pd.read_csv(args.inventory_filename).fillna("")

    # Write and typeset supplies inventory
    tex_filename = "../documents/supplies.tex"
    with open(tex_filename, "w") as fp:
        begin_document(fp)
        fp.write(r"\textbf{supplies}")
        fp.write(r"\newline")
        group_by_location = inventory.sort_values(["ord", "item"]).groupby("location")
        group_names = [
            "fridge",
            "tall cabinet",
            "tea and coffee cabinet",
            "cooking cabinet",
            "cooking drawer",
            "trash cabinet",
            "sink cabinet",
            "bathroom closet",
            "snack station",
            "basement stair landing",
            "basement shelves",
            "freezer",
            "laundry",
            "bathroom cabinet",
        ]
        n_inner_rows = int(group_by_location.size().median())
        write_group_by(fp, group_by_location, group_names, n_inner_rows)
        end_document(fp)
    run(["pdflatex", tex_filename], cwd="../documents")

    # Write and typeset shopping lists
    for store in inventory["store"].unique():
        tex_filename = (
            "../documents/" + store.replace(" ", "_").replace("'", "") + ".tex"
        )
        with open(tex_filename, "w") as fp:
            begin_document(fp)
            fp.write(r"\textbf{" + f"{store}" + r"}")
            fp.write(r"\newline")
            group_by_store = (
                inventory[inventory["store"] == store][inner_cols + ["department"]]
                .drop_duplicates()
                .sort_values("item")
                .groupby("department")
            )

            # Order department by store
            if store == "market basket":
                group_names = [
                    "service",
                    "dairy & eggs",
                    "meat",
                    "condiments",
                    "baking",
                    "pasta",
                    "pharmacy",
                    "paper",
                    "wraps",
                    "cleaning",
                    "water",
                    "freezer",
                    "fruits & vegetables",
                ]
                n_inner_rows = 17
            elif store == "trader joe's":
                group_names = [
                    "fruits & vegetables",
                    "cheese & crackers",
                    "coffee & tea",
                    "dairy & eggs",
                    "nuts & dried fruit",
                    "staples",
                    "bread",
                    "pharmacy",
                    "chocolate, cookies & crackers",
                ]
                n_inner_rows = 11

            else:
                group_names = [name for name, group in group_by_store]
                n_inner_rows = 15

            write_group_by(
                fp, group_by_store, group_names, n_inner_rows, write_rule=True
            )
            end_document(fp)
        run(["pdflatex", tex_filename], cwd="../documents")


if __name__ == "__main__":
    main()
