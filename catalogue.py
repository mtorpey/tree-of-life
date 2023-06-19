# get file from https://www.catalogueoflife.org/data/download
# documentation at https://github.com/CatalogueOfLife/coldp#nameusage

import csv
from pypersist import persist

DATA_FILE = "catalogue-of-life/NameUsage.tsv"

@persist
def make_forest(filename):
    taxa_by_id = read_taxa(DATA_FILE)
    nodes_by_id = dict()
    root_ids = []
    for taxon_id in taxa_by_id:
        taxon = taxa_by_id[taxon_id]
        node = {"name": taxon["name"], "children": []}
        nodes_by_id[taxon_id] = node

    for taxon_id in taxa_by_id:
        parent_id = taxa_by_id[taxon_id]["parent_id"]
        if parent_id == "":
            print(taxon_id)
            root_ids.append(taxon_id)
        else:
            nodes_by_id[parent_id]["children"].append(nodes_by_id[taxon_id])

    return [nodes_by_id[root_id] for root_id in root_ids]


def read_taxa(filename):
    with open(filename, "r") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)

        i = 0
        taxa_by_id = dict()

        for record in reader:
            this_id = record["col:ID"]
            parent_id = record["col:parentID"]
            status = record["col:status"]
            if status == "accepted" or status == "provisionally accepted":
                name = record["col:scientificName"]
                taxon = {"name": name, "parent_id": parent_id}
                taxa_by_id[this_id] = taxon
            i += 1
            #if i > 100000:
                #break  # sample the file
            if i % 10000 == 0:
                print(i / 50000, "%", end="\r")

    print("Loaded")
    return taxa_by_id


def get_subtree_from_forest(forest, root):
    for tree in forest:
        if (subtree := get_subtree(tree, root)) is not None:
            return subtree
    return None


def get_subtree(tree, root):
    if tree["name"] == root:
        return tree
    for child in tree["children"]:
        if (out := get_subtree(child, root)) is not None:
            return out
    return None

def get_tree(root):
    forest = make_forest(DATA_FILE)
    return get_subtree_from_forest(forest, root)
