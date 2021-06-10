import re
from pathlib import Path

from cgcrepair.core.corpus.snippet import Snippet

START = "^#(if|ifndef|ifdef) PATCHED"
CHANGE = "#(else|elseif|elif)"
END = "#endif"


def line_indentation(line: str):
	return line[0:line.find(line.lstrip())] + "\n"


class SourceFile:
	def __init__(self, file_path: Path):
		self.path = file_path
		self.snippets = []

		with self.path.open(mode="r") as file:
			self.lines = file.readlines()

		self.total_lines = len(self.lines)
		self.removed = False
		self.vuln_lines = 0
		self.patch_lines = 0

		self.extract_snippets()

	def __len__(self):
		return len(self.snippets)

	def has_snippets(self):
		return len(self) > 0

	def extract_snippets(self):
		snippet = None

		for i, line in enumerate(self.lines):
			stripped = line.strip()
			if snippet is None:
				match = re.search(START, stripped)
				if match:
					snippet = Snippet(i)
					snippet(state="patch")
					self.snippets.append(snippet)
			else:
				match = re.search(CHANGE, stripped)
				if match:
					snippet.change = i
					snippet(state="vuln")
				elif stripped.startswith(END):
					snippet.end = i
					snippet = None
				else:
					snippet(line=line)

					if snippet.state == "patch":
						self.patch_lines += 1
					else:
						self.vuln_lines += 1

	def remove_patch(self):
		# copy of lines
		if self.removed:
			return

		aux_lines = self.lines.copy()
		# this shift is used to keep track of where patches started after removing them from code
		shift = 0

		# plus one because list starts at 0 and line number starts with 1
		for snippet in self.snippets:
			if snippet.change is not None:
				patch_size = snippet.change - (snippet.start + 1)
				aux_lines[snippet.change] = "\n"
				# snippet.change -= (patch_size + shift + 1)
				snippet.change += 1
			else:
				patch_size = snippet.end - (snippet.start + 1)

			aux_lines[snippet.start: snippet.start+1+patch_size] = ["\n"] * (patch_size + 1)
			snippet.start += 1
			aux_lines[snippet.end] = "\n"
			#snippet.start -= shift
			#snippet.end -= (shift + patch_size + 1)
			snippet.end -= 1
			shift += patch_size

		#self.lines = list(filter(None, aux_lines))
		self.lines = aux_lines
		self.removed = True

		with self.path.open(mode="w") as new_file:
			new_file.writelines(self.lines)

	def get_patch(self) -> dict:
		patch = {}

		for snippet in self.snippets:

			if snippet.change is not None:
				fix = self.lines[snippet.start+1:snippet.change]
			else:
				fix = self.lines[snippet.start+1:snippet.end]

			patch[snippet.start+1] = fix if fix else [' ']

		return patch

	def get_vuln_hunks(self) -> str:
		vuln_hunks = ""

		for snippet in self.snippets:
			if snippet.change:
				if snippet.start == snippet.end:
					vuln_hunks += f"{snippet.change+1},{snippet.end+1};"
				else:
					vuln_hunks += f"{snippet.change+1},{snippet.end};"
			else:
				if snippet.start == snippet.end:
					vuln_hunks += f"{snippet.start+1},{snippet.end+1};"
				else:
					vuln_hunks += f"{snippet.start+1},{snippet.end};"

		return vuln_hunks

	def get_vuln(self) -> dict:
		vuln = {}

		for snippet in self.snippets:
			if snippet.change is not None:
				if snippet.change == snippet.end:
					vuln[snippet.change+1] = self.lines[snippet.change:snippet.end+1]
				else:
					vuln[snippet.change+1] = self.lines[snippet.change+1:snippet.end]
			else:
				vuln[snippet.end+1] = [' ']

		return vuln
