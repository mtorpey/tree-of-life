import sys
import catalogue, wikispecies

COMPRESS_SEPARATOR = " → "

def compress_tree(tree, show_all=True):
    while len(tree["children"]) == 1 and not is_leaf(tree["children"][0]):
        child = tree["children"][0]
        tree["children"] = child["children"]
        if show_all:
            tree["name"] += COMPRESS_SEPARATOR + child["name"]
        else:
            tree["name"] = child["name"]

    for child in tree["children"]:
        compress_tree(child, show_all)


def is_leaf(tree):
    return len(tree["children"]) == 0


def print_tree(tree, indent=0, name_lookup=dict(), html=False, output=print):
    name = tree["name"]
    children = tree["children"]
    display_string = typeset_taxon_chain(name.replace("_", " "), name_lookup, html)
    is_leaf = len(children) == 0
    if html:
        if is_leaf:
            line = "<div>" + display_string + "</div>\n"
        else:
            line = "<details open>\n<summary>" + display_string + "</summary>\n"
    else:
        line = indent * "│ " + display_string
    output(line)
    for child in children:
        print_tree(child, indent + 1, name_lookup, html, output)
    if html and not is_leaf:
        output("</details>\n")


def typeset_taxon_chain(chain, name_lookup, html):
    taxa = chain.split(COMPRESS_SEPARATOR)
    outputs = [typeset_taxon(taxon, name_lookup, html) for taxon in taxa]
    return COMPRESS_SEPARATOR.join(outputs)


def typeset_taxon(scientific, name_lookup, html):
    scientific_display = abbrev_species_name(scientific)
    if scientific in name_lookup:
        common_name = name_lookup[scientific]
    elif (api_common_name := wikispecies.get_common_name(scientific)) is not None:
        common_name = api_common_name
        name_lookup[scientific] = api_common_name  # for future runs
    else:
        common_name = None

    if html:
        if common_name is None:
            common_html = ""
        else:
            common_html = f'<span class="common">{common_name}</span> '
        return common_html + f'<span class="scientific">{scientific_display}</span>'
    else:
        return f"{common_name} ({scientific_display})" if common_name else scientific_display


def abbrev_species_name(name):
    parts = name.split(" ")

    if len(parts) == 2:
        genus, species = parts
        if genus.istitle() and species.islower():
            return genus[0] + ". " + species
    elif len(parts) == 3:
        genus, species, subspecies = parts
        if genus.istitle() and species.islower() and subspecies.islower():
            return genus[0] + ". " + species[0] + ". " + subspecies
        
    return name


def pruned_tree(tree, leaves):
    name = tree["name"]
    if name in leaves:  # discard children
        return {"name": name, "children": []}

    children = tree["children"]
    pruned_children = []

    for child in children:
        subtree = pruned_tree(child, leaves)
        if subtree is not None:
            pruned_children.append(subtree)

    if len(pruned_children) == 0:
        return None

    return {"name": name, "children": pruned_children}


# parse user args
root = sys.argv[1]
if len(sys.argv) == 3 and "." in sys.argv[2]:
    targets = [line.strip().split(",")[0] for line in open(sys.argv[2], "r").readlines()]
    common_names = [tuple(line.strip().split(",")) for line in open(sys.argv[2], "r").readlines()]
    name_lookup = dict()
    for scientific, common in common_names:
        name_lookup[scientific] = common
elif len(sys.argv) > 1:
    targets = sys.argv[2:]
else:
    targets = None

# Handle underscores
# Only needed for wikispecies
#if targets:
#    targets = [name.replace(" ", "_") for name in targets]

# make tree structure
tree = catalogue.get_tree(root)
if targets:
    tree = pruned_tree(tree, targets)
compress_tree(tree, show_all=True)

# print to screen
print_tree(tree, name_lookup=name_lookup)

# print to file
with open("out.html", "w") as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Tree of life</title>
    <meta name="color-scheme" content="light dark">
    <link rel="stylesheet" href="tree-of-life.css">
  </head>
  <body>""")
    print_tree(tree, name_lookup=name_lookup, html=True, output=f.write)
    f.write("""</body>
</html>""")
