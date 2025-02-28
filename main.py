import os

from collections import defaultdict
from copy import copy
from time import time
from sys import getrecursionlimit, setrecursionlimit

class LosslessCompressor:

	'''
	### Lossless Compressor

	#### Info

	Compresses and uncompresses text files using a recursive lossless compression algorithm.

	#### Perameters
	- `mode: int -> 0 or 1` - 0 = priotise byte size when compressing, 1 = prioritise number of characters

	#### Attributes
	- `text_delimeter: str` - delimeter used to separate lookup table items in output
	- `lookup_delimeter: str` - delimeter used to separate lookup table items in output
	- `lookup_key_prefix: str` - mode = 0: the character that prefixes another character representing a chunk, so the program knows that it represents another chunk
							   - mode = 1: the program works backwards through unicode characters, beginning with this one, to represent chunks in the output
	'''
	
	def __init__(self, mode: int = 0) -> None:

		self.mode = mode
		self.text_delimeter = chr(0)
		self.lookup_delimeter = chr(1)
		self.lookup_key_prefix = chr(2) if not self.mode else chr(1114111)

	def compress(self, paths: list[str]) -> None:

		'''
		#### Info
		Compresses each file in the `paths` perameter and saves it to the `compressed/` folder <br>
		Prints details about the output;
		- time taken
		- % compression (bytes + chars)
		- file size (new vs original) - bytes
		- % size of lookup table

		#### Perameters
		- `paths: list[str]` - list of paths to files to compress

		#### Returns
		- (Nothing - the output is saved to `compressed/` folder automatically)
		'''

		def gen_output(text: str, lookup: dict[str, str]) -> str:

			'''
			#### Info
			Concatenates the lookup dictionary and compressed text in the correct format to be saved.
			- Uses `self.text_delimeter` to seperate the lookup dictionary from the text
			- Uses `self.lookup_delimeter` to seperate each key and value pair in the lookup dictionary

			#### Perameters
			- `text: str` - the compressed text to use in the output
			- `lookup: dict[str, str]` - the chunk lookup dictionary to use in the output

			#### Returns
			- `str` - a string of the concatenated lookup dictionary and text
			'''

			lookup_output = (self.lookup_delimeter.join([f'{item[0]}{item[1]}' for item in lookup.items()]) + f'{self.text_delimeter}') if lookup else ''
			return lookup_output + text

		def gen_hash_table(text: str, chunk_len: int) -> defaultdict[str, list[int]]:

			'''
			#### Info
			Generates a super-fast lookup dictionary containing all `chunk_len` chunks in `text` and their indexes. <br>

			#### Perameters
			- `text: str` - the text of which to analyse chunks and their indexes
			- `chunk_len: int` - the length of chunks analysed in the text

			#### Returns	 
			- `defaultdict[str, list[int]]` - a dictionary whose keys are the chunks, and the values their indexes (`chunk_indexes: list = outputted_dict[chunk: str]`)
			'''

			hash_table = defaultdict(list)

			for i in range(len(text) - chunk_len + 1):

				chunk = text[i:i + chunk_len]
				hash_table[chunk].append(i)
				
			return hash_table

		def compress(prev_text: str, prev_lookup: dict) -> tuple[str, dict[str, str]]:

			'''
			#### Info
			- The recursive compression algorithm that uses lossless compression.
			'''

			compressed_text = copy(prev_text)
			lookup = copy(prev_lookup)

			chunk_len = 2 if self.mode else 3
			hash_table = gen_hash_table(text = compressed_text, chunk_len = chunk_len)

			for chunk_index in range(len(compressed_text) - chunk_len):
				
				chunk = compressed_text[chunk_index: chunk_index + chunk_len]
				duplicate_indexes = [i for i in hash_table.get(chunk, []) if i != chunk_index]
			
				if duplicate_indexes:
		
					char = chr(ord(self.lookup_key_prefix) - len(lookup)) if self.mode else chr(ord(self.lookup_key_prefix) + 1 + len(lookup))
					more = True
					temp_len = chunk_len
					prev_same_count = 0

					while more:
						
						temp_len += 1
						temp_chunk = compressed_text[chunk_index: chunk_index + temp_len]
						duplicate_indexes = [i for i in duplicate_indexes if compressed_text[i: i + temp_len] == temp_chunk and i != chunk_index]

						if len(duplicate_indexes) >= prev_same_count and duplicate_indexes: chunk = temp_chunk
						else: more = False

						prev_same_count = len(duplicate_indexes)
					
					lookup[char] = chunk
					compressed_text = compressed_text.replace(chunk, (char) if self.mode else (self.lookup_key_prefix + char))

					try: next_compressed_text, next_lookup = compress(prev_text = compressed_text, prev_lookup = lookup)
					except RecursionError:
						setrecursionlimit(getrecursionlimit() + 1) 
						next_compressed_text, next_lookup = compress(prev_text = compressed_text, prev_lookup = lookup)

					output = gen_output(text = compressed_text, lookup = lookup)
					next_output = gen_output(text = next_compressed_text, lookup = next_lookup)

					original_size = len(input_text) if self.mode else len(input_text.encode())
					output_size = len(output) if self.mode else len(output.encode())
					next_output_size = len(next_output) if self.mode else len(next_output.encode())

					percent_compression = self.percentage_change(mode = 0, original = original_size, new = output_size)
					next_percent_compression = self.percentage_change(mode = 0, original = original_size, new = next_output_size)
					
					if percent_compression < 0 and next_percent_compression < 0: return prev_text, prev_lookup
					if lookup: return [(compressed_text, lookup), (next_compressed_text, next_lookup)][percent_compression <= next_percent_compression]
			
			return prev_text, prev_lookup

		for path in paths:

			output_path = f'compressed/{os.path.splitext(os.path.basename(path))[0]}.llc'

			print(f'\ncompressing {path} -> {output_path} (mode = {['bytes', 'characters'][self.mode]});')

			start_time = time()
			input_text = self.read_file(path)
			
			compressed_text, lookup = compress(prev_text = input_text, prev_lookup = {})
			output_text = gen_output(text = compressed_text, lookup = lookup)

			original_size = len(input_text) if self.mode else len(input_text.encode())
			output_size = len(output_text) if self.mode else len(output_text.encode())

			percent_compression = self.percentage_change(mode = 0, original = original_size, new = output_size)

			lookup_percentage = round(len(lookup) / len(compressed_text) * 100, 2) if self.mode else round(len(compressed_text.split(self.text_delimeter)[0].encode()) / len(compressed_text.encode()) * 100, 2)

			self.save_file(output_path, output_text)

			print(f'completed successfully ({round(time() - start_time, 2)}s);')
			print(f'| (lookup table {lookup_percentage}% of output)')
			print('| percentage compresssion')

			if self.mode:
				print(f'| - chars: {round(percent_compression, 2)}%')
			else:
				print(f'| - bytes: {round(percent_compression, 2)}%')
				print('| file size')
				print(f'| - original: {original_size} bytes')
				print(f'| - compressed: {output_size} bytes')

	def uncompress(self, paths: list[str]) -> None:

		def extract_output(input_compressed: str) -> tuple[str, dict[str, str]]:

			'''
			#### Info
			Takes the compressed output and extracts the compressed text and lookup dictionary

			#### Perameters
			- `output: str` = the raw output from the saved file

			#### Returns
			- `tuple[` <br>
			  `    str,` = compressed text <br>
			  `    dict[str, str]` = lookup dictionary <br>
			  `]`
			'''

			lookup = {x[0]: x[1:] for x in input_compressed.split(self.text_delimeter)[0].split(self.lookup_delimeter)}
			text = '\n'.join(input_compressed.split(self.text_delimeter)[1:])

			return text, lookup

		for path in paths:

			if os.path.splitext(os.path.basename(path))[1] != '.llc': raise ValueError(f'file {path} is not a .llc file; please enter a valid .llc file path')

			output_path = f'uncompressed/{os.path.splitext(os.path.basename(path))[0]}.txt'

			print(f'\nuncompressing {path} -> {output_path};')

			start_time = time()
			input_compressed = self.read_file(path = path)
			text, lookup = extract_output(input_compressed)

			for char, chunk in list(lookup.items())[-1::-1]: text = text.replace(self.lookup_key_prefix + char, chunk)
				
			chars_uncompression = (len(text) - len(input_compressed)) / len(input_compressed) * 100
			self.save_file(path = output_path, contents = text)

			original_size = os.stat(path).st_size
			output_size = os.stat(output_path).st_size

			chars_uncompression = self.percentage_change(mode = 1, original = len(input_compressed), new = len(text))
			bytes_uncompression = self.percentage_change(mode = 1, original = original_size, new = output_size)

			print(f'completed successfully ({round(time() - start_time, 2)}s);')
			print('| percentage uncompresssion')
			print(f'| - bytes: {round(bytes_uncompression, 2)}%')
			print(f'| - chars: {round(chars_uncompression, 2)}%')
			print('| file size')
			print(f'| - original: {original_size} bytes')
			print(f'| - compressed: {output_size} bytes')
	
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