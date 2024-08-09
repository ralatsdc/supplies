import os

import pandas as pd

n_outer_rows = 3
n_outer_cols = 4

inner_cols = ["qty", "unt", "item"]
inner_algn = " c c l "


def escape_specials(values):
    if len(values) == 1:
        return str(values[0]).replace("%", r"\%").replace("&", r"\&")
    else:
        return [str(value).replace("%", r"\%").replace("&", r"\&") for value in values]

def print_outer_cell(fp, group, n_inner_rows, name=None, print_rule=False):

    fp.write(r"    \begin{tabular}[t]{" + inner_algn + "}\n")
    fp.write(r"    \\" + "\n")
    if name:
        fp.write(r"    \multicolumn{" + str(len(inner_cols)) + r"}{l}{\textbf{" + escape_specials([name]) + r"}} \\" + "\n")
        fp.write(r"    \hline" + "\n")
        fp.write(r"    \\" + "\n")
        n_inner_rows -= 2
        
    n_inner_row = 0
    indexes = []

    for index, row in group.iterrows():
        if print_rule:
            fp.write(r"    \rule[0pt]{0.25in}{0.5pt} &" + " & ".join(escape_specials(row[inner_cols[1:]].values)))

        else:
            fp.write("      " + " & ".join(escape_specials(row[inner_cols].values)))

        n_inner_row += 1
        indexes.append(index)

        if n_inner_row < n_inner_rows and n_inner_row < group.shape[0]:
            fp.write(r" \\" + "\n")

        else:
            break

    fp.write("\n" + r"    \end{tabular}" + "\n")

    return group.drop(index=indexes)



def print_group_by(fp, group_by_label, group_names, n_inner_rows, print_rule=False):

    fp.write(r"  \begin{tabular}[t]{" + " p{2.5in} " * n_outer_cols + "}\n")

    n_outer_row = 0
    n_outer_col = 0

    current_group_name = ""
    for name in group_names:
        group = group_by_label.get_group(name)
        
        while group.shape[0] > 0:

            if name == current_group_name:
                group = print_outer_cell(fp, group, n_inner_rows, print_rule=print_rule)

            else:
                current_group_name = name
                group = print_outer_cell(fp, group, n_inner_rows, name=current_group_name, print_rule=print_rule)

            n_outer_col += 1

            if n_outer_col < n_outer_cols:
                # if group.shape[0] > 0 or name != last_group_name:
                if group.shape[0] > 0 or name != group_names[-1]:
                    fp.write("    &\n")

            else:

                n_outer_row += 1

                if n_outer_row < n_outer_rows:
                    fp.write(r"  \\" + "\n")
                    fp.write(r"  \\" + "\n")

                    n_outer_col = 0

            if n_outer_row == n_outer_rows and n_outer_col == n_outer_cols:

                n_outer_row = 0
                n_outer_col = 0

                fp.write(r"  \end{tabular}" + "\n")

                # if group.shape[0] > 0 or name != last_group_name:
                if group.shape[0] > 0 or name != group_names[-1]:

                    fp.write(r"  \begin{tabular}[t]{" + " p{2.5in} " * n_outer_cols + "}\n")

            # elif group.shape[0] == 0 and name == last_group_name:
            elif group.shape[0] == 0 and name == group_names[-1]:

                fp.write(r"  \end{tabular}" + "\n")


def main():

    inventory_filename = "../resources/inventory-2024-08-09.csv"

    inventory = pd.read_csv(inventory_filename).fillna("")

    suplies_filename = os.path.basename(inventory_filename).replace(".csv", ".tex")

    with open(suplies_filename, "w") as fp:

        fp.write(r"\documentclass{article}" + "\n")
        fp.write(r"\usepackage{array}" + "\n")
        fp.write(r"\usepackage{geometry}" + "\n")
        fp.write(r"\geometry{letterpaper, landscape, margin=0.25in}" + "\n")
        fp.write(r"\begin{document}" + "\n")

        group_by_location = inventory.groupby("location")
        group_names = [
            'fridge',
            'tall cabinet',
            'tea and coffee cabinet',
            'cooking cabinet',
            'cooking drawer',
            'trash cabinet',
            'sink cabinet',
            'bathroom closet',
            'snack station',
            'basement stair landing',
            'basement shelves',
            'freezer',
            'laundry',
            'bathroom cabinet',
            ]
        n_inner_rows = int(group_by_location.size().median())
        print_group_by(fp, group_by_location, group_names, n_inner_rows)

        fp.write(r"\newpage" + "\n")

        group_by_store = inventory[inventory["store"] == "market basket"][inner_cols + ["department"]].drop_duplicates().groupby("department")
        group_names = [
            'service',
            'dairy & eggs',
            'meat',
            'condiments',
            'baking',
            'pasta',
            'pharmacy',
            'paper',
            'wraps',
            'cleaning',
            'water',
            'freezer',
            'fruits & vegetables',
            ]
        n_inner_rows = 20
        print_group_by(fp, group_by_store, group_names, n_inner_rows, print_rule=True)

        fp.write(r"\newpage" + "\n")

        group_by_store = inventory[inventory["store"] == "trader joe's"][inner_cols + ["department"]].drop_duplicates().groupby("department")
        group_names = [
            'staples',
            'fruits & vegetables',
            'cheese & crackers',
            'chocolate, cookies & crackers',
            'nuts & dried fruit',
            'dairy & eggs',
            'bread',
            'coffee & tea',
            'pharmacy',
            ]
        n_inner_rows = 20
        print_group_by(fp, group_by_store, group_names, n_inner_rows, print_rule=True)

        fp.write(r"\end{document}" + "\n")


if __name__ == "__main__":
    main()
