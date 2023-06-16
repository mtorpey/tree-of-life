# get file from https://www.catalogueoflife.org/data/download
# documentation at https://github.com/CatalogueOfLife/coldp#nameusage

import csv

with open("catalogue-of-life/NameUsage.tsv", "r") as f:
    reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
    records = []
    types = set()
    i = 0
    for record in reader:
        types.add(record["col:rank"])
        print(i/50000, "%", end="\r")
        i += 1
        

    print(len(records))
    print(types)
