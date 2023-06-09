import re, requests, sys
from pypersist import persist

API_URL = "https://species.wikimedia.org/w/api.php"
COMPRESS_SEPARATOR = " → "

links = dict()
lines = [line.strip() for line in open("tree-data.txt", "r")]

# process data into dictionary
for line in lines:
    m = re.fullmatch("^(.*) -> (.*)$", line.strip())
    parent = m.group(1)
    child = m.group(2)
    if parent not in links:
        links[parent] = set()
    links[parent].add(child)
print(len(links), "nodes in tree")

def make_tree(links, start):
    tree = dict()
    if start not in links:
        return None
    for child in links[start]:
        tree[child] = make_tree(links, child)
    return tree

def compress_tree(tree, show_all=True):
    while True:
        new_tree = tree.copy()
        changed = False
        for child_key, child_value in tree.items():
            if child_value is not None and len(child_value) == 1:
                grandchild_key, grandchild_value = list(child_value.items())[0]
                if grandchild_value is not None:
                    del new_tree[child_key]
                    if show_all:
                        new_key = child_key + COMPRESS_SEPARATOR + grandchild_key
                    else:
                        new_key = grandchild_key  # only display most specific taxon
                    new_tree[new_key] = grandchild_value
                    changed = True
        tree.clear()
        tree.update(new_tree)
        if not changed:
            break
    
    for child in tree:
        if tree[child] is not None:
            compress_tree(tree[child], show_all)

def print_tree(tree, indent=0, name_lookup=dict(), html=False, output=print):
    for child in tree:
        display_string = typeset_taxon_chain(child.replace("_", " "), name_lookup, html)
        if html:
            if tree[child] is None:
                line = "<div>" + display_string + "</div>\n"
            else:
                line = "<details open>\n<summary>" + display_string + "</summary>\n"
        else:
            line = indent * "│ " + display_string
        output(line)
        if tree[child] is not None:
            print_tree(tree[child], indent + 1, name_lookup, html, output)
        if html:
            if tree[child] is not None:
                output("</details>\n")

def typeset_taxon_chain(chain, name_lookup, html):
    taxa = chain.split(COMPRESS_SEPARATOR)
    outputs = [typeset_taxon(taxon, name_lookup, html) for taxon in taxa]
    return COMPRESS_SEPARATOR.join(outputs)

def typeset_taxon(scientific, name_lookup, html):
    scientific_display = abbrev_species_name(scientific)
    if scientific in name_lookup:
        common_name = name_lookup[scientific]
    elif (api_common_name := get_common_name(scientific)) is not None:
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
    if tree is None:
        return None
    pruned = dict()
    for child in tree:
        if child in leaves:
            pruned[child] = None
        else:
            subtree = pruned_tree(tree[child], leaves)
            if subtree is not None:
                pruned[child] = subtree
    if len(pruned) == 0:
        return None
    return pruned

@persist
def get_common_name(species):
    # Parameters for the API request
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": species,
        "rvslots": "*",
        "rvprop": "content",
        "format": "json",
        "formatversion": "2"
    }

    try:
        # Send the GET request
        response = requests.get(API_URL, params=params)
        response.raise_for_status()  # Check for any request errors
        data = response.json()
        page = data["query"]["pages"][0]
        content = page["revisions"][0]["slots"]["main"]["content"]
        start = content.find("{{VN")
        start = content.find("|en=", start)
        if start == -1:
            return None
        start += len("|en=")
        next_lang = content.find("|", start)
        end_of_vn = content.find("}}", start)
        if next_lang == -1:
            end = end_of_vn
        else:
            end = min(next_lang, end_of_vn)
        common_name = content[start:end].strip()
        return common_name

    except (requests.exceptions.RequestException, KeyError) as e:
        return None

# parse user args
top = sys.argv[1]
if len(sys.argv) == 3 and "." in sys.argv[2]:
    targets = [line.strip().split(",")[1] for line in open(sys.argv[2], "r").readlines()]
    common_names = [tuple(line.strip().split(",")) for line in open(sys.argv[2], "r").readlines()]
    name_lookup = dict()
    for common, scientific in common_names:
        name_lookup[scientific] = common
elif len(sys.argv) > 1:
    targets = sys.argv[2:]
else:
    targets = None

if targets:
    targets = [name.replace(" ", "_") for name in targets]

# make tree structure
tree = {top: make_tree(links, top)}
if targets:
    tree = pruned_tree(tree, targets)

compress_tree(tree, show_all=True)

print_tree(tree, name_lookup=name_lookup)

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
