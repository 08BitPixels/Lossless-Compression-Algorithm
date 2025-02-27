import os

from collections import defaultdict
from copy import copy
from time import time
from sys import getrecursionlimit, setrecursionlimit

class LosslessCompressor:
	
	def __init__(self) -> None:

		self.lookup_delimeter = chr(1)
		self.text_delimeter = chr(0)
		self.lookup_key_start = chr(1114111)
		self.recursion_limit = getrecursionlimit()

	def compress(self, paths: list[str]) -> None:

		def gen_output(text: str, lookup: dict) -> str:

			lookup_output = (self.lookup_delimeter.join([f'{item[0]}{item[1]}' for item in lookup.items()]) + f'{self.text_delimeter}') if lookup else ''
			return lookup_output + text

		def gen_hash_table(text: str, chunk_len: int) -> defaultdict[str, list[int]]:

			hash_table = defaultdict(list)

			for i in range(len(text) - chunk_len + 1):

				chunk = text[i:i + chunk_len]
				hash_table[chunk].append(i)
				
			return hash_table

		def compress(prev_text: str, prev_lookup: dict) -> tuple[str, dict[str, str]]:

			compressed_text = copy(prev_text)
			lookup = copy(prev_lookup)
			hash_table = gen_hash_table(text = compressed_text, chunk_len = 2)

			for chunk_index in range(len(compressed_text) - 2):
				
				chunk = compressed_text[chunk_index: chunk_index + 2]
				duplicate_indexes = [i for i in hash_table.get(chunk, []) if i != chunk_index]
			
				if duplicate_indexes:
		
					char = chr(ord(self.lookup_key_start) - len(lookup))
					more = True
					temp_len = 2
					prev_same_count = 0

					while more:
						
						temp_len += 1
						temp_chunk = compressed_text[chunk_index: chunk_index + temp_len]
						duplicate_indexes = [i for i in duplicate_indexes if compressed_text[i: i + temp_len] == temp_chunk and i != chunk_index]

						if len(duplicate_indexes) >= prev_same_count and duplicate_indexes: chunk = temp_chunk
						else: more = False

						prev_same_count = len(duplicate_indexes)
					
					lookup[char] = chunk

					compressed_text = compressed_text.replace(chunk, char)
					try: next_compressed_text, next_lookup = compress(prev_text = compressed_text, prev_lookup = lookup)
					except RecursionError:
						self.recursion_limit *= 10
						setrecursionlimit(self.recursion_limit) 
						next_compressed_text, next_lookup = compress(prev_text = compressed_text, prev_lookup = lookup)

					output = gen_output(text = compressed_text, lookup = lookup)
					next_output = gen_output(text = next_compressed_text, lookup = next_lookup)

					chars_compression = self.percentage_change(mode = 0, original = len(input_text), new = len(output))
					next_chars_compression = self.percentage_change(mode = 0, original = len(input_text), new = len(next_output))
					
					if chars_compression < 0 and next_chars_compression < 0: return prev_text, prev_lookup
					if lookup: return [(compressed_text, lookup), (next_compressed_text, next_lookup)][chars_compression <= next_chars_compression]
			
			return prev_text, prev_lookup

		for path in paths:

			output_path = f'compressed/{os.path.splitext(os.path.basename(path))[0]}.llc'

			print(f'\ncompressing {path} -> {output_path};')

			start_time = time()
			input_text = self.read_file(path)
			
			compressed_text, lookup = compress(prev_text = input_text, prev_lookup = {})
			output_text = gen_output(text = compressed_text, lookup = lookup)
			
			self.save_file(output_path, output_text)

			original_size = os.stat(path).st_size
			output_size = os.stat(output_path).st_size

			chars_compression = self.percentage_change(mode = 0, original = len(input_text), new = len(output_text))
			bytes_compression = self.percentage_change(mode = 0, original = original_size, new = output_size)

			print(f'completed successfully ({round(time() - start_time, 2)}s);')
			print(f'| original size: {original_size} bytes')
			print(f'| compressed size: {output_size} bytes')
			print(f'| bytes: compressed by {round(bytes_compression, 2)}%')
			print(f'| chars: compressed by {round(chars_compression, 2)}%')

	def uncompress(self, paths: list[str]) -> None:

		for path in paths:

			if os.path.splitext(os.path.basename(path))[1] != '.llc': raise ValueError(f'file {path} is not a .llc file; please enter a valid .llc file path')

			output_path = f'uncompressed/{os.path.splitext(os.path.basename(path))[0]}.txt'

			print(f'\nuncompressing {path} -> {output_path};')

			start_time = time()
			input_compressed = self.read_file(path = path)
			lookup = {x[0]: x[1:] for x in input_compressed.split(self.text_delimeter)[0].split(self.lookup_delimeter)}
			text = '\n'.join(input_compressed.split(self.text_delimeter)[1:])

			for key, item in list(lookup.items())[-1::-1]: text = text.replace(key, item)
				
			chars_uncompression = (len(text) - len(input_compressed)) / len(input_compressed) * 100
			self.save_file(path = output_path, contents = text)

			original_size = os.stat(path).st_size
			output_size = os.stat(output_path).st_size

			chars_uncompression = self.percentage_change(mode = 1, original = len(input_compressed), new = len(text))
			bytes_uncompression = self.percentage_change(mode = 1, original = original_size, new = output_size)

			print(f'completed successfully ({round(time() - start_time, 2)}s);')
			print(f'| original size: {original_size} bytes')
			print(f'| uncompressed size: {output_size} bytes')
			print(f'| bytes: uncompressed by {round(bytes_uncompression, 2)}%')
			print(f'| chars: uncompressed by {round(chars_uncompression, 2)}%')
	
	def read_file(self, path: str) -> str: 

		if os.path.isfile(path): 

			file = open(path, 'r', encoding = 'utf-8')
			contents = file.read()
			file.close()
			return contents
		
		else: 
			raise FileNotFoundError(f'file \'{path}\' not found; please enter a valid file path')

	def save_file(self, path: str, contents: str) -> None:

		def save() -> None:

			file = open(path, 'w', encoding = 'utf-8')
			file.write(contents)
			file.close()

		if os.path.isfile(path): 
			save()
		else:
			if not os.path.isdir(os.path.dirname(path)): os.makedirs(os.path.dirname(path))
			save()

	def percentage_change(self, mode: int, original: float, new: float) -> float:

			'''
			mode: 0 or 1; 0 = decrease, 1 = increase
			'''

			difference = new - original if mode else original - new
			return (difference / original) * 100

def main() -> None:

	compressor = LosslessCompressor()
	compressor.compress(paths = ['input.txt'])

if __name__ == '__main__': main()