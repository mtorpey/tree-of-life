import re, requests, sys
from pypersist import persist

API_URL = "https://species.wikimedia.org/w/api.php"

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

def print_tree(tree, indent=0, name_lookup=dict(), html=False, output=print):
    for child in tree:
        scientific = child.replace("_", " ")
        scientific_display = scientific
        if tree[child] is None:
            scientific_display = abbrev_species_name(scientific_display)
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
            html_name = common_html + f'<span class="scientific">{scientific_display}</span>'
                
            if tree[child] is None:
                line = "<div>" + html_name + "</div>\n"
            else:
                line = "<details open>\n<summary>" + html_name + "</summary>\n"
        else:
            display_name = (common_name + " - " if common_name else "") + scientific_display
            line = indent * "│ " + display_name
        output(line)
        if tree[child] is not None:
            print_tree(tree[child], indent + 1, name_lookup, html, output)
        if html:
            if tree[child] is not None:
                output("</details>\n")

def abbrev_species_name(name):
    try:
        genus, species = name.split(" ")
        return genus[0] + ". " + species
    except ValueError:
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

@persist(
    key=lambda s: s,
    hash=lambda s: s,
    pickle=lambda n: n if n else "NO_COMMON_NAME",
    unpickle=lambda v: None if v == "NO_COMMON_NAME" else v
)
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
