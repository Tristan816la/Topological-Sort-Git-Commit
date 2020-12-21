# Keep the function signature,
# but replace its body with your implementation.
#
# Note that this is the driver function.
# Please write a well-structured implemention by
# creating other functions outside of this one,
# each of which has a designated purpose.
#
# As a good programming practice,
# please do not use any script-level variables that are modifiable.
# This is because those variables live on
# forever once the script is imported,
# and the changes to them will persist
# across different invocations of the imported functions.


# Notice on line 87 I used decode("cp437"), if it doesn't work,
# Change it to decode()


# Usage of Strace
# 1. I first use command
# ``which git``
# and know my git is in directory /usr/local/cs/bin/git
# 2. Then I use
# ```strace -o debug.txt python3 topo_order_commits.py```
# to write the out put of system calls to a file called debug.txt
# 3. Then I use the command
# ``cat debug.txt | grep "/usr/local/cs/bin/git"``
# and found no git command was invoked
#
# If git was invoked, there should be an entry
# "execve("/usr/local/cs/bin/git",..."" like this


import sys
import os
from os.path import dirname
from os import path
from os import walk
from zlib import decompress
from collections import defaultdict
# TODO: change recursion limit using sys and modify test_example_repos.py to
# pass all the test cases
# Notice this file cannot contain any word about recursion limit so
# I cannot show you
# the exact command to set the recursion limit


def topo_order_commits():

    class CommitNode:
        def __init__(self, commit_hash):
            """
            :type commit_hash: str
            """
            self.commit_hash = commit_hash
            self.parents = set()
            self.children = set()

    current_path = os.getcwd()
    git_path = ""

    # 1. Find .git location
    if path.exists(f"{current_path}/.git"):
        git_path = f"{current_path}/.git"
    else:  # Find from parents
        p = dirname(current_path)
        while dirname(p):
            if path.exists(f"{p}/.git"):
                git_path = f"{p}/.git"
                break
            elif p == "/":
                if path.exists(f"{p}.git"):
                    git_path = f"{p}/.git"
                break
            p = dirname(p)

    if not git_path:
        sys.stderr.write("Not inside a Git repository")
        exit(1)

    # 2.1. Get the list of branch names
    branch_path = f"{git_path}/refs/heads"
    branches = []
    for (dirpath, dirnames, filenames) in walk(branch_path):
        relative_path = dirpath.replace(branch_path, "")
        if relative_path:
            # [1:] to avoid the forward slash in relative path
            branch_names = [relative_path[1:] + "/" + f for f in filenames]
            branches.extend(branch_names)
        else:
            branches.extend(filenames)

    # 2.2. Decompress the objects
    object_path = f"{git_path}/objects"
    objects = defaultdict(str)  # store hash -> value in the dict
    for(dirpath, dirnames, filenames) in walk(object_path):
        if dirpath == object_path:
            continue
        for file in filenames:
            filename = f"{dirpath}/{file}"
            key = dirpath[-2:] + file
            compressed_content = open(filename, 'rb').read()
            objects[key] = decompress(compressed_content).decode("cp437")

    # 3. Build the commit graph
    # 3.1 Filter out the commits
    commits = defaultdict(str)
    for obj, objval in objects.items():
        if "commit" in objval[:6]:
            commits[obj] = objval

    # 3.2 Build the commit graph
    root_commits = []
    created = defaultdict(CommitNode)  # Store the created nodes

    def dfs_generate(root_hash):
        if root_hash not in created:
            root = CommitNode(root_hash)
            created[root_hash] = root
        else:
            root = created[root_hash]

        meta_info = commits[root_hash]
        lines = meta_info.splitlines()

        for line in lines:
            if "parent" in line[:6]:
                _, parent_hash = line.split(" ")
                # Create a parent node
                if parent_hash not in created:
                    parent = CommitNode(parent_hash)
                    created[parent_hash] = parent
                    root.parents.add(parent_hash)
                    parent.children.add(root_hash)
                else:
                    parent = created[parent_hash]
                    parent.children.add(root.commit_hash)
                    root.parents.add(parent_hash)

        # Base case
        if not root.parents and root not in root_commits:
            root_commits.append(root)
        else:
            for parent_hash in sorted(root.parents):
                dfs_generate(parent_hash)

    branch_heads = defaultdict(set)  # store this for step 5

    for branch in branches:
        branch_head_file = open(f"{branch_path}/{branch}", "r")
        branch_hash = branch_head_file.read().rstrip()
        dfs_generate(branch_hash)
        branch_heads[branch_hash].add(branch)

    # 4. Topological ordering
    order = []

    def dfs_topsort(v, visited, order):
        visited.add(v.commit_hash)
        for child in v.children:
            if child not in visited:
                dfs_topsort(created[child], visited, order)
        order.append(v)

    for root in root_commits:
        dfs_topsort(root, set(), order)

# 5. Print out the topological ordering
    sticky = False
    for i, node in enumerate(order):
        node_hash = node.commit_hash
        if sticky:
            sticky = False
            print("=", end="")
            for child in node.children:
                print(created[child].commit_hash, end=" ")
            print()

        if node_hash in branch_heads:
            names = sorted(branch_heads[node_hash])
            print(node_hash, end=" ")
            for name in names:
                print(name, end=" ")
            print()
        else:
            print(node_hash)

        if i < len(order) - 1 and order[i + 1].commit_hash not in node.parents:
            for i, parent in enumerate(node.parents):
                if i == len(node.parents) - 1:
                    print(parent, end="")
                else:
                    print(parent, end=" ")
            print("=")
            print()
            sticky = True


if __name__ == '__main__':
    topo_order_commits()
