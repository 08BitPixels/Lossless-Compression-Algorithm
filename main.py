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
	- `mode: int (0 or 1)` - `0` = priotise file size when compressing; `1` = prioritise number of characters

	#### Attributes
	- `mode: int (0 or 1)` - `0` = priotise file size when compressing; `1` = prioritise number of characters
	- `text_delimeter: str` - delimeter used to separate the text and lookup table in output
	- `lookup_delimeter: str` - delimeter used to separate lookup table items in output
	- `lookup_key_prefix: str`;
		- when `mode = 0`: the character that prefixes another character representing a chunk, so the program knows that it represents another chunk
		- when `mode = 1`: the program works backwards through unicode characters, beginning with this one, to represent chunks in the output
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
		- `paths: list[str]` - list of paths of files to compress

		#### Returns
		- (Nothing - the output is saved to the `compressed/` folder automatically)
		'''

		# SUBFUNCTIONS
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

			lookup_output = self.lookup_delimeter.join([item[0] + item[1] for item in lookup.items()]) # joins each key and chunk together, and joins them with self.lookup_delimeter
			return lookup_output + self.text_delimeter + text

		def gen_hash_table(text: str, chunk_len: int) -> defaultdict[str, list[int]]:

			'''
			#### Info
			Generates a super-fast lookup dictionary containing all chunks of len `chunk_len` in `text` and their indexes. <br>

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
			- The recursive compression algorithm function that creates lossless compression.

			#### Perameters
			- `prev_text: str`: the previous compressed / uncompressed text to be compressed again
			- `prev_lookup: str`: the previous lookup dictionary to be extended

			#### Returns
			- `tuple[` <br>
			  `    str,` - the text that has been compressed <br>
			  `    dict[str, str],` - the lookup dictionary containing their keys and the chunks they represent <br>
			  `]`
			'''

			text = copy(prev_text)
			lookup = copy(prev_lookup)

			chunk_len = 2 if self.mode else 3 # when mode = 0 -> lookup key len = 2 -> can only check for chunks of len greater (otherwise inf recursion)
			hash_table = gen_hash_table(text = text, chunk_len = chunk_len)

			for chunk_index in range(len(text) - chunk_len + 1): # loops through every chunk index
				
				chunk = text[chunk_index: chunk_index + chunk_len]
				duplicate_indexes = [i for i in hash_table.get(chunk, []) if i != chunk_index]
			
				if duplicate_indexes: # if chunk has duplicates -> continue, else skip to next chunk len
		
					key = chr(ord(self.lookup_key_prefix) + 1 + len(lookup)) if not self.mode else chr(ord(self.lookup_key_prefix) - len(lookup)) # char used to represent chunk; when mode = 0 -> chars start from start of unicode, work forwards; when mode = 1 -> chars start from end of unicode, work backwards
					
					# extends chunk len and checks if still same amount of duplicates, until num of duplicates decreases
					more = True
					temp_len = chunk_len
					prev_same_count = 0

					while more:
						
						temp_len += 1
						temp_chunk = text[chunk_index: chunk_index + temp_len]
						duplicate_indexes = [i for i in duplicate_indexes if text[i: i + temp_len] == temp_chunk]

						if len(duplicate_indexes) >= prev_same_count and duplicate_indexes: chunk = temp_chunk
						else: more = False

						prev_same_count = len(duplicate_indexes)
					
					lookup[key] = chunk # adds char + chunk to lookup dict
					text = text.replace(chunk, (key) if self.mode else (self.lookup_key_prefix + key)) # replaces chunk in text with char; when mode = 1 -> keys only 1 char, when mode = 0 -> keys 2 chars

					# generates current output + details
					output = gen_output(text = text, lookup = lookup) # puts text + lookup into output format
					output_size = len(output) if self.mode else len(output.encode())
					percent_compression = self.percentage_change(mode = 0, original = input_size, new = output_size)

					# compresses again (extends recursion limit if necessary)
					try: 
						text_next, lookup_next = compress(prev_text = text, prev_lookup = lookup)

					except RecursionError: 
						setrecursionlimit(getrecursionlimit() + 1) 
						text_next, lookup_next = compress(prev_text = text, prev_lookup = lookup)
				
					# generates next output + detals
					output_next = gen_output(text = text_next, lookup = lookup_next)
					output_size_next = len(output_next) if self.mode else len(output_next.encode())
					percent_compression_next = self.percentage_change(mode = 0, original = input_size, new = output_size_next)
					
					# compares current + next output, returns one with higher % compression
					if percent_compression < 0 and percent_compression_next < 0: return prev_text, prev_lookup
					if lookup: return [(text, lookup), (text_next, lookup_next)][percent_compression <= percent_compression_next]
			
			return prev_text, prev_lookup # no compression found
		# ------------

		for path in paths: # compresses each file in paths

			output_path = f'compressed/{os.path.splitext(os.path.basename(path))[0]}.llc'

			print(f'\ncompressing {path} -> {output_path} (mode: {['bytes', 'characters'][self.mode]});')

			# retreives input data
			start_time = time()
			input_text = self.read_file(path)

			# input details
			input_len = len(input_text)
			input_size = len(input_text.encode())
			
			# compresses input
			compressed_text, lookup = compress(prev_text = input_text, prev_lookup = {})
			output_text = gen_output(text = compressed_text, lookup = lookup)

			# output details
			output_len = len(output_text)
			output_size = len(output_text.encode())

			percent_compression_bytes = self.percentage_change(mode = 0, original = input_size, new = output_size)
			percent_compression_chars = self.percentage_change(mode = 0, original = input_len, new = output_len)

			lookup_percentage = round(len(compressed_text.split(self.text_delimeter)[0]) / len(output_text) * 100, 2) if self.mode else round(len(compressed_text.split(self.text_delimeter)[0].encode()) / len(output_text.encode()) * 100, 2)

			self.save_file(output_path, output_text)

			# prints compression details
			print(f'completed successfully ({round(time() - start_time, 5)}s);')
			print('| percentage compresssion:')

			if self.mode: # mode: chars

				print(f'| - chars: {round(percent_compression_chars, 2)}%')
				print(f'| - (bytes: {round(percent_compression_bytes, 2)}%)')
				print('| number of chars:')
				print(f'| - original: {input_len} chars')
				print(f'| - compressed: {output_len} chars')

			else: # mode: bytes

				print(f'| - bytes: {round(percent_compression_bytes, 2)}%')
				print(f'| - (chars: {round(percent_compression_chars, 2)}%)')
				print('| file size')
				print(f'| - original: {input_size} bytes')
				print(f'| - compressed: {output_size} bytes')

			print(f'| (lookup table {lookup_percentage}% of output)')
			
	def uncompress(self, paths: list[str]) -> None:

		'''
		#### Info
		Unompresses each file in the `paths` perameter and saves it as a .llc (.losslesscompressed) to the `uncompressed/` folder <br>
		Prints details about the output;
		- time taken
		- % uncompression (bytes + chars)
		- file size (new vs original) - bytes

		#### Perameters
		- `paths: list[str]` - list of paths of files to uncompress

		#### Returns
		- (Nothing - the output is saved to the `uncompressed/` folder automatically)
		'''

		# SUBFUNCTIONS
		def extract_input(input: str) -> tuple[str, dict[str, str]]:

			'''
			#### Info
			Takes the compressed input and extracts the compressed text and lookup dictionary
			- Uses `self.text_delimeter` to seperate the lookup dictionary from the text
			- Uses `self.lookup_delimeter` to seperate each key and value pair in the lookup dictionary

			#### Perameters
			- `output: str` = the raw output from the saved file

			#### Returns
			- `tuple[` <br>
			  `    str,` = compressed text <br>
			  `    dict[str, str]` = lookup dictionary <br>
			  `]`
			'''

			if self.mode: lookup = {x[0]: x[1:] for x in input.split(self.text_delimeter)[0].split(self.lookup_delimeter)} # if chars mode: keys only 1 char long
			elif not self.mode: lookup = {x[0:1]: x[1:] for x in input.split(self.text_delimeter)[0].split(self.lookup_delimeter)} # if bytes mode: keys 2 chars long (prefix + ascii char)
			text = '\n'.join(input.split(self.text_delimeter)[1:])

			return text, lookup
		
		def uncompress(input: str) -> str:

			'''
			#### Info
			Takes the raw input, extracts the text an lookup dict, and replaces all compressed chars with their corresponding chunks

			#### Perameters
			- `input: str` - the raw input text from the .llc file

			#### Returns
			- `str` - the uncompressed text
			'''

			text, lookup = extract_input(input_text)
			print(text, lookup)

			# works backwards through lookup and replaces all chars with their corresponding chunks
			for key, chunk in list(lookup.items())[-1::-1]: text = text.replace([(self.lookup_key_prefix + key), key][self.mode], chunk) # mode = 1 -> key only 1 char, mode = 0 -> key 2 chars 

			return text
		# ------------

		for path in paths: # uncompresses each file in paths

			# checks if file to uncompress is a .llc file
			if os.path.splitext(os.path.basename(path))[1] != '.llc': raise ValueError(f'file {path} is not a .llc file; please enter a valid .llc file path')

			output_path = f'uncompressed/{os.path.splitext(os.path.basename(path))[0]}.txt'

			print(f'\nuncompressing {path} -> {output_path};')

			# retreives input data
			start_time = time()
			input_text = self.read_file(path = path)

			# input details
			input_len = len(input_text)
			input_size = len(input_text.encode())

			# uncompresses text
			output = uncompress(input = input_text)

			# output details
			output_len = len(output)
			output_size = len(output.encode())

			percent_compression_bytes = self.percentage_change(mode = 1, original = input_size, new = output_size)
			percent_compression_chars = self.percentage_change(mode = 1, original = input_len, new = output_len)

			self.save_file(path = output_path, contents = output)

			# prints uncompression details
			print(f'completed successfully ({round(time() - start_time, 5)}s);')
			print('| percentage uncompresssion:')

			if self.mode:

				print(f'| - chars: {round(percent_compression_chars, 2)}%')
				print(f'| - (bytes: {round(percent_compression_bytes, 2)}%)')
				print('| number of chars:')
				print(f'| - compressed: {input_len} chars')
				print(f'| - uncompressed: {output_len} chars')

			else:

				print(f'| - bytes: {round(percent_compression_bytes, 2)}%')
				print(f'| - (chars: {round(percent_compression_chars, 2)}%)')
				print('| file size')
				print(f'| - compressed: {input_size} bytes')
				print(f'| - uncompressed: {output_size} bytes')
	
	def read_file(self, path: str) -> str: 

		'''
		#### Info
		Reads a file at `path`, and returns its contents if the file exists else raises a FileNotFoundError

		#### Perameters
		- `path: str` - the path of the file to read

		#### Returns
		- `str` - the raw contents of the file
		'''

		if not os.path.isfile(path): raise FileNotFoundError(f'file \'{path}\' not found; please enter a valid file path')

		file = open(path, 'r', encoding = 'utf-8')
		contents = file.read()
		file.close()
		return contents
			
	def save_file(self, path: str, contents: str) -> None:

		'''
		#### Info
		Saves a file at `path` with contents `contents`, and makes the file and folder if they do not exist already

		#### Perameters
		- `path: str` - the path of the file to save
		- `contents: str` - the contents to save in the file

		#### Returns
		- (Nothing)
		'''

		if not os.path.isdir(os.path.dirname(path)): os.makedirs(os.path.dirname(path)) 
		
		file = open(path, 'w', encoding = 'utf-8')
		file.write(contents)
		file.close()

	def percentage_change(self, mode: int, original: float, new: float) -> float:

			'''
			#### Info
			Calculates the percentage increase / decrease from `original` and `new`.

			#### Perameters
			- `mode: int (0 or 1)` - 0 = calculate percentage decrease; 1 = calculate percentage increase
			- `original: float` - the original number for the calculation
			- `new: float` - the new number to calculate the percentage change from `original`

			#### Returns
			- `float` - the percentage increase / decrease from `original` to `new`
			'''

			difference = new - original if mode else original - new
			return (difference / original) * 100

def main() -> None:

	compressor = LosslessCompressor(mode = 0)
	compressor.compress(paths = ['input.txt'])

if __name__ == '__main__': main()