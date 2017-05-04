import optparse

def create_iln_gatk_dict(illumina):
	'''
	create a dictionary which stores chr,pos:ref,alt,depth
	from illumina vcf called by GATK
	'''
	dict = {}
	infile = open(illumina,'r')
	lines = infile.readlines()
	infile.close()
	
	for i in lines:
		if i.startswith("#"):#skip comment lines
			continue
		else:
			col = i.strip().split("\t")
			key = ("\t").join(col[:2])#key is "chr\tpos"
			iln_ref = col[3]#retrieve illumina reference allele
			iln_alt = col[4]#retrieve illumina alternative allele
			if iln_alt == ".":#if ref allele, value is ref allele + "."
				print col
				depth = col[9].split(":")[1] #read depth for GATK ref allele
                                value = ("\t").join([iln_ref,iln_alt,depth])
				dict[key] = value

			elif len(iln_alt) < 2:#hom 1/1 or het 0/1
				info = col[9]
				gt = info.split(":")[0]#genotype info, i.e 0/0 or 1/1
				depth = info.split(":")[1]#the depth info
				depth_col = depth.split(",")
				ref_depth = depth_col[0]#reference allele depth
				alt_depth = depth_col[1]#alternative allele depth
				value = ("\t").join([iln_ref,iln_alt,ref_depth,alt_depth,gt])	
				dict[key] = value

			else:#het 1/2
				info = col[9]
                                gt = info.split(":")[0]#genotype info 1/2
                                depth = info.split(":")[1]#the depth info
				depth_col = depth.split(",")
                                ref_depth = depth_col[0]#reference allele depth
                                alt1_depth = depth_col[1]#1st alternative allele depth
				alt2_depth = depth_col[2]#2nd alternative allele depth
                                value = ("\t").join([iln_ref,iln_alt,ref_depth,alt1_depth,alt2_depth,gt])
                                dict[key] = value
				
	return dict


def create_iln_bcftools_dict(illumina):
	'''
	create a dictionary which stores chr,pos:ref,alt,depth
	from illumina vcf called by bcftools
	'''
	dict = {}
	infile = open(illumina,'r')
	lines = infile.readlines()
	infile.close()
	
	for i in lines:
		if i.startswith("#"):#skip comment lines
			continue
		else:
			col = i.strip().split("\t")
			key = ("\t").join(col[:2])#key is "chr\tpos"
			iln_ref = col[3]#retrieve illumina reference allele
			iln_alt = col[4]#retrieve illumina alternative allele
			info = col[7].split(";")
			depth = info[0].split("=")[-1]
			dp4 = info[-2].split("=")[-1].split(",")#extract dp4 info 
			ref_fwd = int(dp4[0])#depth of ref allele supported by fwd read
			ref_rev = int(dp4[1])#depth of ref allele supported by rev read
			alt_fwd = int(dp4[2])#depth of alt allele supported by fwd read
			alt_rev = int(dp4[3])#depth of alt allele supported by rev read
			if iln_alt == ".":#if ref allele, value is ref allele + "."
				print col
                                value = ("\t").join([iln_ref,iln_alt,depth])
				dict[key] = value

			elif len(iln_alt) < 2:#hom 1/1 or het 0/1
				gt = col[9].split(":")[0]#genotype info, i.e 0/0 or 1/1
				ref_depth = str(ref_fwd + ref_rev)#reference allele depth
				alt_depth = str(alt_fwd + alt_rev)#alternative allele depth
				value = ("\t").join([iln_ref,iln_alt,ref_depth,alt_depth,gt])	
				dict[key] = value
	return dict


def create_np_bcftools_dict(nanopore):
	'''
        create a dictionary which stores chr,pos:ref,alt,depth
        from nanopore vcf called by bcftools
        '''
	dict = {}
	infile = open(nanopore,'r')
	lines = infile.readlines()
	infile.close()
	
	for i in lines:
		if i.startswith("#"): #skip comment lines
                        continue
		else:
			col = i.strip().split("\t")
                        key = ("\t").join(col[:2]) #key is "chr\tpos"
                        np_ref = col[3] #retrieve nanopore reference allele
                        np_alt = col[4] #retrieve nanopore alternative allele	
			dp_info = col[7].split(";")[0]
			depth = dp_info.split("=")[-1] #read depth for nanopore ref or alt allele
			value = ("\t").join([np_ref,np_alt,depth])
			dict[key] = value
	return dict


def compare_hom_vcf(illumina,nanopore,ref,alt,refCaller):
	if refCaller:#ref .vcf is called by GATK
		print "creating illumina gatk dictionary"
		iln_dict = create_iln_gatk_dict(illumina)
	else:#ref .vcf is called by bcftools
		print "creating illumina bcftools dictionary"
		iln_dict = create_iln_bcftools_dict(illumina)
	 
	np_dict = create_np_bcftools_dict(nanopore)
	
	outlist = []
	
	for i in np_dict:
		if not(i in iln_dict):
			print "i isn't in the dictionary"
			continue #skip the pos if it's not found in illumina dict
		else:
			np_snp = np_dict[i] #get nanopore snp info from dictionary
			np_col = np_snp.split("\t") #split it by tab
			np_ref = np_col[0]
			np_alt = np_col[1]
			np_depth = np_col[2]
			
			iln_snp = iln_dict[i] #get illumina snp info from dictionary
			iln_col = iln_snp.split("\t")
			iln_ref = iln_col[0]
			iln_alt = iln_col[1]
			
			if (len(np_ref)>1) or (len(np_alt)>1) or (len(iln_ref)>1) or (len(iln_alt)>1):
				continue #skip if it's INDEL

			elif (np_alt == ".") and (iln_alt == "."):
				ref_depth = int(iln_col[2])
				if (ref_depth < ref):
					continue #skip if GATK ref allele depth is less than ref cutoff
				else:
					out_element = ("\t").join([i,np_depth,"TN"])#write True Negative
					outlist.append(out_element)
			elif (np_alt != ".") and (iln_alt != ".") and (np_alt != iln_alt):
				continue #skip if both aren't reference allele and np alt is different from illumina alt

			elif (np_alt == iln_alt): #True positive, nanopore alt is same as illumina alt
				ref_depth = int(iln_col[2]) #illumina reference allele read depth
				alt_depth = int(iln_col[3]) #illumina alternative allele read depth
				if (ref_depth > ref) or (alt_depth < alt):
					continue #skip if illumina snp is before cutoff
				else:
					out_element = ("\t").join([i,np_depth,"TP"])#write True Positive
					outlist.append(out_element)

			elif (np_alt == ".") and (iln_alt != "."):
				ref_depth = int(iln_col[2]) #illumina reference allele read depth
                                alt_depth = int(iln_col[3]) #illumina alternative allele read depth
				if (ref_depth > ref) or (alt_depth < alt):
                                        continue #skip if illumina snp is below cutoff
				else:
					out_element = ("\t").join([i,np_depth,"FN"])#write False Negative
					outlist.append(out_element)

			elif (np_alt != ".") and (iln_alt == "."):
				out_element = ("\t").join([i,np_depth,"FP"])#write False Positive
				outlist.append(out_element)

	return outlist	

def main(illumina,nanopore,ref,alt,hom,refCaller,outfile):
	print "running main function"
	if hom:
		print "running homozygous"
		outlist = compare_hom_vcf(illumina,nanopore,ref,alt,refCaller)
	out_file = open(outfile,'w')
	out_file.write("#CHR\tPOS\tTotalReads\tInfo\n")
	for i in outlist:
		out_file.write(i+"\n")#write each snp with TP/FP/FN to the out_file
	out_file.close()

if __name__== '__main__':
	'''
	Generates true positive, false positive, false negative snps by comparing
	vcf homozygous sites generated by GATK (illumina data) and Nanopolish (nanopore data)
	'''
    	# parser object for managing input options
	parser = optparse.OptionParser()

    	# essential data
	parser.add_option( '-i' , dest = 'illumina' ,
                default = '' ,
                help = 'the illumina vcf generated by GATK. Make sure to delete rows with missing data. i.e ./.' )
	
	parser.add_option( '-n' , dest = 'nanopore' ,
                default = '' ,
                help = 'the nanopore vcf called by bcftools' )
	
	parser.add_option( '-r' , dest = 'ref', type="int",
                default = 0 ,
                help = 'the ref allele depth cutoff (<=) for GATK (AD), default = 0' )
	
	parser.add_option( '-a' , dest = 'alt', type="int",
                default = 5 ,
                help = 'the alternative allele depth cutoff (>=) for GATK (AD), default = 5' )
		
	parser.add_option("-m" , action = "store_true",
                dest = "hom",
                help = "use this option to compare homozygous sites between nanopolish and GATK")
	
	parser.add_option("-g", action = "store_true",
		dest = "refCaller",
		help = "use this option to read ref .vcf called by GATK")

	parser.add_option("-b", action = "store_false",
		dest = "refCaller",
		help = "use this option to read ref .vcf called by bcftools")
	
	parser.add_option( '-o' , dest = 'outfile' ,
               	default = 'bcftools_accuracy.txt' ,
	        help = 'specify the output file, which stores true positive, false positive, false negative info')

    	# load the inputs
	(options , args) = parser.parse_args()
    
    	# process the inputs
	illumina = options.illumina
	nanopore = options.nanopore
	ref = options.ref
	alt = options.alt
	refCaller = options.refCaller
	hom = options.hom
	outfile = options.outfile
	main(illumina,nanopore,ref,alt,hom,refCaller,outfile)
