import sys, re

links = dict()
lines = [line.strip() for line in open("PRUNED.txt", "r")]

for line in lines:
    m = re.fullmatch("^(.*) -> (.*)$", line.strip())
    parent = m.group(1)
    child = m.group(2)
    if parent not in links:
        links[parent] = set()
    links[parent].add(child)

print(len(links), "nodes in tree\n")

def tree_closure(links, start, allowed):
    pruned = {start: set()}
    if start not in links:
        return None
    for child in links[start]:
        if allowed is None or child in allowed:
            pruned[start].add(child)
            if (subtree := tree_closure(links, child, allowed)) is not None:
                pruned.update(subtree)
        elif (subtree := tree_closure(links, child, allowed)) is not None:
            pruned[start].add(child)
            pruned.update(subtree)
    if len(pruned[start]) == 0:
        return None
    return pruned

def print_tree(links, start, indent=0):
    print(indent * "│ " + start.replace("_", " "))
    if start in links:
        for child in links[start]:
            print_tree(links, child, indent + 1)

def parent(links, child):
    for x in links:
        if child in links[x]:
            return x

top = sys.argv[1]
targets = [name.replace(" ", "_") for name in sys.argv[2:]]

#for name in targets:
#    print(f"(parent {parent(links, name)})")
#    print_tree(links, name)
#    print()

pruned = tree_closure(links, top, targets)

print_tree(pruned, top)
