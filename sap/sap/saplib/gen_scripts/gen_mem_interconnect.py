import gen
import saputils
from string import Template
from string import atoi
from gen import Gen

class GenInterconnect(Gen):


	def __init__(self):
		print "in GenInterconnect"
		return

	def gen_script (self, tags = {}, buf = "", debug=False):
		"""Overridden function"""
		slave_list = []
		template = Template(buf)
		
		port_buf = ""
		port_def_buf = ""
		mem_select_buf = ""
		assign_buf = ""
		data_block_buf = ""
		ack_block_buf = ""
		int_block_buf = ""
		param_buf = ""

		#start with 1 to account for DRT
		num_slaves = 0
		if (tags.has_key("MEMORY")):
			#got a list of all the slaves to add to make room for
			slave_list = tags["MEMORY"]	
			num_slaves = num_slaves + len(slave_list)

		if debug:
			for key in tags["MEMORY"]:
				print key + ":" + str(tags["MEMORY"][key])

		slave_keywords = [
				"DRT_ID",
				"DRT_FLAGS",
				"DRT_SIZE"
		]

		mem_offset = 0
		#generate the parameters
		for i in range(0, num_slaves):
			key = tags["MEMORY"].keys()[i]
			absfilename = saputils.find_rtl_file_location(tags["MEMORY"][key]["filename"])
			slave_tags = saputils.get_module_tags(filename = absfilename, bus = "wishbone", keywords = slave_keywords)
			print "slave tags: " + str(slave_tags)
			
			mem_size = slave_tags["keywords"]["DRT_SIZE"].strip()
			
			param_buf = param_buf + "parameter MEM_SEL_" + str(i) + "\t=\t" + str(i) + ";\n"
			param_buf = param_buf + "parameter MEM_OFFSET_" + str(i) + "\t=\t" + str(mem_offset) + ";\n"
			param_buf = param_buf + "parameter MEM_SIZE_" + str(i) + "\t=\t" + mem_size + ";\n"
			mem_offset += atoi(mem_size)
			



		#generate the memory select logic
		mem_select_buf =  "reg [31:0] mem_select;\n"

		mem_select_buf += "\n"
		mem_select_buf += "always @(posedge clk) begin\n"
		mem_select_buf += "\tif (rst) begin\n"
		mem_select_buf += "\t\t//nothing selected\n"
		mem_select_buf += "\t\tmem_select <= 32'hFFFF\n"
		mem_select_buf += "\tend\n"
		mem_select_buf += "\telse begin\n"
		for i in range (num_slaves):
			mem_select_buf += "\t\tif (wbs_addr_i >= MEM_OFFSET_" + str(i) + " && wbs_addr_i < (MEM_OFFSET_" + str(i) + " + MEM_SIZE_" + str(i) + ") begin\n"
			mem_select_buf += "\t\t\tmem_select <= MEM_SEL_" + str(i) + ";\n"
			mem_select_buf += "\t\tend\n"
		mem_select_buf += "\tend\n"
		
		
		

		#for i in range ( 0, num_slaves):
		#	print "count: " + str(i)

		# ports
		for i in range (0, num_slaves):
			port_buf = port_buf + "\ts" + str(i) + "_we_o,\n"
			port_buf = port_buf + "\ts" + str(i) + "_cyc_o,\n"
			port_buf = port_buf + "\ts" + str(i) + "_stb_o,\n"
			port_buf = port_buf + "\ts" + str(i) + "_sel_o,\n"
			port_buf = port_buf + "\ts" + str(i) + "_ack_i,\n"
			port_buf = port_buf + "\ts" + str(i) + "_dat_o,\n"
			port_buf = port_buf + "\ts" + str(i) + "_dat_i,\n"
			port_buf = port_buf + "\ts" + str(i) + "_adr_o,\n"
			port_buf = port_buf + "\ts" + str(i) + "_int_i"

			if (i < num_slaves - 1):
				port_buf = port_buf + ",\n"
				
			port_buf = port_buf + "\n\n"
			

		# port defines
		for i in range (0, num_slaves):
			port_def_buf = port_def_buf + "output\t\t\ts" + str(i) + "_we_o;\n"
			port_def_buf = port_def_buf + "output\t\t\ts" + str(i) + "_cyc_o;\n"
			port_def_buf = port_def_buf + "output\t\t\ts" + str(i) + "_stb_o;\n"
			port_def_buf = port_def_buf + "output\t[3:0]\t\ts" + str(i) + "_sel_o;\n"
			port_def_buf = port_def_buf + "output\t[31:0]\t\ts" + str(i) + "_adr_o;\n"
			port_def_buf = port_def_buf + "output\t[31:0]\t\ts" + str(i) + "_dat_o;\n"
			port_def_buf = port_def_buf + "input\t[31:0]\t\ts" + str(i) + "_dat_i;\n"
			port_def_buf = port_def_buf + "input\t\t\ts" + str(i) + "_ack_i;\n"
			port_def_buf = port_def_buf + "input\t\t\ts" + str(i) + "_int_i;\n"
			port_def_buf = port_def_buf + "\n\n"
		
		
		#assign defines
		for i in range (0, num_slaves):
			assign_buf = assign_buf + "assign s" + str(i) + "_we_o\t=\t(slave_select == MEM_SEL_" + str(i) + ") ? m_we_i: 0;\n"
			assign_buf = assign_buf + "assign s" + str(i) + "_stb_o\t=\t(slave_select == MEM_SEL_" + str(i) + ") ? m_stb_i: 0;\n"
			assign_buf = assign_buf + "assign s" + str(i) + "_sel_o\t=\t(slave_select == MEM_SEL_" + str(i) + ") ? m_sel_i: 0;\n"
			assign_buf = assign_buf + "assign s" + str(i) + "_cyc_o\t=\t(slave_select == MEM_SEL_" + str(i) + ") ? m_cyc_i: 0;\n"
			assign_buf = assign_buf + "assign s" + str(i) + "_adr_o\t=\t(slave_select == MEM_SEL_" + str(i) + ") ? m_adr_i: 0;\n"
			assign_buf = assign_buf + "assign s" + str(i) + "_dat_o\t=\t(slave_select == MEM_SEL_" + str(i) + ") ? m_dat_i: 0;\n"
			assign_buf = assign_buf + "\n"

		#data in block
		data_block_buf = "//data in from slave\n"	
		data_block_buf = data_block_buf + "always @ (slave_select"
		for i in range (0, num_slaves):
			data_block_buf = data_block_buf + " or s" + str(i) + "_dat_i"
		data_block_buf = data_block_buf + ") begin\n\tcase (slave_select)\n"
		for i in range (0, num_slaves):
			data_block_buf = data_block_buf + "\t\tMEM_SEL_" + str(i) + ": begin\n\t\t\tm_dat_o <= s" + str(i) + "_dat_i;\n\t\tend\n";
		data_block_buf = data_block_buf + "\t\tdefault: begin\n\t\t\tm_dat_o <= 32\'hx;\n\t\tend\n\tendcase\nend\n\n"

		#ack in block
		ack_block_buf = "//ack in from slave\n\n"	
		ack_block_buf = ack_block_buf + "always @ (slave_select"
		for i in range (0, num_slaves):
			ack_block_buf = ack_block_buf + " or s" + str(i) + "_ack_i"
		ack_block_buf = ack_block_buf + ") begin\n\tcase (slave_select)\n"
		for i in range (0, num_slaves):
			ack_block_buf = ack_block_buf + "\t\tMEM_SEL_" + str(i) + ": begin\n\t\t\tm_ack_o <= s" + str(i) + "_ack_i;\n\t\tend\n";
		ack_block_buf = ack_block_buf + "\t\tdefault: begin\n\t\t\tm_ack_o <= 1\'hx;\n\t\tend\n\tendcase\nend\n\n"


		#int in block
		int_block_buf = "//int in from slave\n\n"	
		int_block_buf = int_block_buf + "always @ (slave_select"
		for i in range (0, num_slaves):
			int_block_buf = int_block_buf + " or s" + str(i) + "_int_i"
		int_block_buf = int_block_buf + ") begin\n\tcase (slave_select)\n"
		for i in range (0, num_slaves):
			int_block_buf = int_block_buf + "\t\tMEM_SEL_" + str(i) + ": begin\n\t\t\tm_int_o <= s" + str(i) + "_int_i;\n\t\tend\n";
		int_block_buf = int_block_buf + "\t\tdefault: begin\n\t\t\tm_int_o <= 1\'hx;\n\t\tend\n\tendcase\nend\n\n"

		print "buf: " + buf

		buf = template.substitute(	PORTS=port_buf, 
									PORT_DEFINES=port_def_buf, 
									MEM_SELECT=mem_select_buf,
									ASSIGN=assign_buf, 
									DATA=data_block_buf, 
									ACK=ack_block_buf, 
									INT=int_block_buf, 
									MEM_PARAMS=param_buf)
		print "buf: " + buf

		return buf

		def get_name (self):
			print "wishbone_mem_interconnect.py"
