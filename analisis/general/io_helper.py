import os

def getMkdir(dirPath: str) -> str:
	if not os.path.exists(dirPath):
		os.mkdir(dirPath)
	return dirPath