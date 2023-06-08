import re, sys

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
        display_name = scientific
        if scientific in name_lookup:
            display_name = name_lookup[scientific]
        if html:
            if tree[child] is None:
                line = "<div>" + display_name + "</div>"
            else:
                line = "<details open><summary>" + display_name + "</summary>"
        else:
            line = indent * "│ " + display_name
        output(line)
        if tree[child] is not None:
            print_tree(tree[child], indent + 1, name_lookup, html, output)
        if html:
            if tree[child] is None:
                output("</div>")
            else:
                output("</details>")

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
    <style>
    details, div {
        border-left: 1px solid black;
        padding-left: 1em;
    }
    summary {
        margin-left: -1em;
        padding-left: 1em;
        color: gray;
    }
    div {
        font-weight: bold;
    }
    </style>
  </head>
  <body>""")
    print_tree(tree, name_lookup=name_lookup, html=True, output=f.write)
    f.write("""</body>
</html>""")
