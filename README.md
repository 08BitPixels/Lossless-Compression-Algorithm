# Lossless Compression Algorithm

A recursive lossless compression algorithm for text. <br>
_Built on Python_

## How to Use
- Put the text files to compress in the `input\` folder.
- Using the _LosslessCompressor_ class, you can compress and decompress the files, by inputting their paths.
- The output will apear in either the `output\` folder as a text file

> [!NOTE]
> Whilst this algorithm compresses the number of characters very well, unfortunately, the fact that it uses very large Unicode chracters means that the file size itself usually increases. Using larger files usually yeilds better results.
