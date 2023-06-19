import requests

API_URL = "https://species.wikimedia.org/w/api.php"
lines = [line.strip() for line in open("tree-data.txt", "r")]

def get_tree_wikispecies(root):
    # process data into dictionary
    for line in lines:
        m = re.fullmatch("^(.*) -> (.*)$", line.strip())
        parent = m.group(1)
        child = m.group(2)
        if parent not in links:
            links[parent] = set()
    links[parent].add(child)
    print(len(links), "nodes in tree")
    return make_tree(links, root)

def make_tree(links, start):
    tree = dict()
    if start not in links:
        return None
    for child in links[start]:
        tree[child] = make_tree(links, child)
    return tree

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
