import json
import sys
from random import randint

def get_basic_blocks(_code):
	"""
	Returns a dictionary of blocks, separated by the function name.
	Each block is a dictionary itself, with keys "instrs" and "successors".
	The "succesors" key will be used when constructing the cfg.
	"""
	blocks = dict()
	for func in _code["functions"]:
		blocks[func["name"]] = {}
		new_block = {"instrs": [], "predecessors": [], "successors": []}
		fun_len = len(func["instrs"]) - 1
		unnamed_blocks_cntr = 0
		cur_label = ""
		for instr_idx, instr in enumerate(func["instrs"]):
			if "label" in instr:
				if not new_block["instrs"] == []:
					to_append = new_block.copy()
					if cur_label == "":
						cur_label = "b" + str(unnamed_blocks_cntr)
						unnamed_blocks_cntr += 1
					blocks[func["name"]][cur_label] = to_append
				new_block = {"instrs": [], "predecessors": [], "successors": []}
				new_block["instrs"] = [instr]
				cur_label = instr["label"]
				continue
			new_block["instrs"].append(instr)
			if is_breaking_block(instr):
				if cur_label == "":
					cur_label = "b" + str(unnamed_blocks_cntr)
					unnamed_blocks_cntr += 1
				to_append2 = new_block.copy()
				blocks[func["name"]][cur_label] = to_append2
				new_block = {"instrs": [], "predecessors": [], "successors": []}
				continue
			if instr_idx == fun_len:
				if cur_label == "":
					cur_label = "b" + str(unnamed_blocks_cntr)
					unnamed_blocks_cntr += 1
				to_append3 = new_block.copy()
				blocks[func["name"]][cur_label] = to_append3
				new_block = {"instrs": [], "predecessors": [], "successors": []}
				continue
		if not new_block["instrs"] == []:
			to_append4 = new_block.copy()
			blocks[func["name"]][cur_label] = to_append4
	return blocks

def is_breaking_block(_instr):
	is_breaking = False
	if _instr["op"] == "jmp" or _instr["op"] == "br" or _instr["op"] == "ret":
		is_breaking = True
	return is_breaking

def get_cfg(_blocks):
	for func_idx, func in enumerate(_blocks):
		for block_idx, block in enumerate(_blocks[func]):
			#print(block)
			if "op" in _blocks[func][block]["instrs"][-1]:
				if _blocks[func][block]["instrs"][-1]["op"] == "jmp" or _blocks[func][block]["instrs"][-1]["op"] == "br":
					_blocks[func][block]["successors"] = _blocks[func][block]["instrs"][-1]["labels"]
					for label in _blocks[func][block]["instrs"][-1]["labels"]:
						_blocks[func][label]["predecessors"].append(block)
				else:
					if block_idx < len(_blocks[func]) - 1:
						temp = list(_blocks[func].keys())
						_blocks[func][block]["successors"].append(temp[block_idx + 1])
						_blocks[func][temp[block_idx + 1]]["predecessors"].append(block)
	return _blocks

def compute_reaching_defs(_cfg, _inputs):
	in_defs = dict()
	out_defs = dict()
	for func_idx, func in enumerate(_cfg):
		in_defs[func] = dict()
		out_defs[func] = dict()
		worklist = list(_cfg[func].keys())
		for block_idx, block in enumerate(worklist):
			if block_idx == 0:
				in_defs[func][block] = _inputs[func]
				out_defs[func][block] = []
			else:
				in_defs[func][block] = []
				out_defs[func][block] = []
		while not worklist == []:
			block = worklist[randint(0, len(worklist) - 1)]
			in_defs[func][block] = df_merge(out_defs[func], _cfg[func][block])
			print(f"The new in_defs for block {block} is {in_defs[func][block]}")
			new_out = df_transfer(in_defs[func][block], _cfg[func][block])
			if not new_out == out_defs[func][block]:
				for successor in _cfg[func][block]["successors"]:
					if not successor in worklist:
						worklist.append(successor)
			else:
				pass
			worklist.remove(block)
			out_defs[func][block] = new_out
	return in_defs, out_defs

def df_merge(_out_defs, _block):
	defs = []
	for block in _block["predecessors"]:
		print(f"block is {block} - union between {defs} and {_out_defs[block]}")
		defs = union(defs, _out_defs[block])
	return defs

def union(a, b):
	dset = set()
	for instr in a:
		dset.add(json.dumps(instr, sort_keys=True))
	for instr in b:
		dset.add(json.dumps(instr, sort_keys=True))
	res = []
	for elem in list(dset):
		res.append(json.loads(elem))
	return res

def df_transfer(_defs, _block):
	def_vars = []
	def_instrs = dict()
	#### Initialize with the input definitions.
	for definition in _defs:
		if not definition["dest"] in def_vars:
			def_vars.append(definition["dest"])
		if not definition["dest"] in def_instrs:
			def_instrs[definition["dest"]] = [definition]
		else:
			print(f"Appending!! {definition}")
			print(def_instrs[definition["dest"]])
			def_instrs[definition["dest"]].append(definition)

	#### Bring in the definitions within the block.
	for _, instr in enumerate(_block["instrs"]):
		if "dest" in instr:
			if not instr["dest"] in def_vars:
				def_vars.append(instr["dest"])
			def_instrs[instr["dest"]] = [instr]
	
	instrs = []
	for elem in list(def_instrs.values()):
		instrs = instrs + elem
				
	return instrs


def get_inputs(_code):
	inputs = dict()
	for _, func in enumerate(_code["functions"]):
		inputs[func["name"]] = []
		if "args" in func:
			for arg in func["args"]:
				inputs[func["name"]].append({"is_input": True, "dest": arg["name"]})
	return inputs

def print_cfg(_cfg):
	for func in _cfg:
		for block in _cfg[func]:
			print(block)
			print(_cfg[func][block]["predecessors"])
			print(_cfg[func][block]["successors"])


if __name__ == "__main__":
	code = json.load(sys.stdin)
	blocks = get_basic_blocks(code)
	#print(blocks)
	cfg = get_cfg(blocks)
	#print(cfg)
	print_cfg(cfg)
	inputs = get_inputs(code)
	#print(inputs)
	in_defs, out_defs = compute_reaching_defs(cfg, inputs)
	for _, func in enumerate(cfg):
		print(f"function is {func}")
		for block in list(cfg[func].keys()):
			print(f"block is {block}")
			print(f"In: {in_defs[func][block]}")
			print(f"Out: {out_defs[func][block]}")
