import optparse
#filter the SNPs identified by bcftools based on DP

def filter_depth(infile,depthCutoff):
	list = []#use a list to store pass-filter lines
	
	inFile = open(infile,'r')
	lines = inFile.readlines()
	inFile.close()
	
	for i in lines:
		if i.startswith("#"):
			list.append(i)#skip comment lines
		else:
			col = i.strip().split("\t")
			gt = col[-1]#genotype info
			info = col[7]
			dp = info.split("DP=")[-1].split(";")[0]#extract DP value
			if gt.startswith("0/0"):
				list.append(i) #add to list if there is no alt allele at this position
			elif gt.startswith("1/1") or gt.startswith("0/1"):
				if (int(dp) >= depthCutoff):
					list.append(i)#add to list if the depth of snp passes filter
				else:
					continue
			else:
				continue#skip if GT is 1/2 (two alt alleles) or ./. (no data)
	return list

def main(infile,depthCutoff,outfile):	
	outList = filter_depth(infile,depthCutoff)
	outFile = open(outfile,'w')
	
	for i in outList:
		outFile.write(i)
	outFile.close()
	
		
if __name__== '__main__':
	'''
	filter the vcf generated by bcftools based on dp4 value
	'''
    	# parser object for managing input options
	parser = optparse.OptionParser()

    	# essential data
	parser.add_option( '-i' , dest = 'infile' ,
                default = '' ,
                help = 'the input i.e. .bcftools.vcf file')
	parser.add_option( '-d' , dest = 'depthCutoff' ,  type="int",
               	default = '2' ,
	        help = 'specify the cutoff for the DP (>=DP). default = 2' )
	parser.add_option( '-o' , dest = 'outfile' ,
                default = '' ,
                help = 'specify output filename, i.e. .bcftools.dp2.vcf' )

    	# load the inputs
	(options , args) = parser.parse_args()
    
    	# process the inputs
    	# note: all commandline inputs are str by default
	infile = options.infile
	depthCutoff = options.depthCutoff
	outfile = options.outfile
	main(infile,depthCutoff,outfile)