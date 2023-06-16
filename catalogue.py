# get file from https://www.catalogueoflife.org/data/download
# documentation at https://github.com/CatalogueOfLife/coldp#nameusage

import csv

def read_taxa(filename):
    with open(filename, "r") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)

        for record in reader:
            for k in record.keys():
                print(k)
            break

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

    return taxa_by_id

def make_tree(taxa_by_id):
    nodes_by_id = dict()
    for taxon_id in taxa_by_id:
        taxon = taxa_by_id[taxon_id]
        node = {"name": taxon["name"], "children": []}
        nodes_by_id[taxon_id] = node
        #print(taxon_id)

    for taxon_id in taxa_by_id:
        parent_id = taxa_by_id[taxon_id]["parent_id"]
        #print(parent_id)
        if parent_id == "":
            print(nodes_by_id[taxon_id])
        else:
            nodes_by_id[parent_id]["children"].append(nodes_by_id[taxon_id])

    print(nodes_by_id["6256T"])

taxa_by_id = read_taxa("catalogue-of-life/NameUsage.tsv")
tree = make_tree(taxa_by_id)
