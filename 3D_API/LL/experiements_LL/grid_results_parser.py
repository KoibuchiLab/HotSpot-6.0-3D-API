#!/usr/bin/python
#quick parser...not good engineering
read_to = open("raw_gird_size_test_results.txt","r")
read_ll = open("raw_gird_size_test_results_LL.txt","r")
write_to = open("avg_grid_size_test_results.txt","w+")
write_ll = open("avg_grid_size_test_results_LL.txt","w+")
raw_to = read_to.readlines()
raw_ll = read_ll.readlines()

write_to.write(raw_to[0])
write_to.write(raw_to[1])
write_ll.write(raw_ll[0])
write_ll.write(raw_ll[1])

#print len(raw_to)
#print len(raw_ll)
grid_size = -1

output_to = -1
avg_time_to = []
avg_l1_to = []
avg_llc_to = []

output_ll = -1
avg_time_ll = []
avg_l1_ll = []
avg_llc_ll = []

count = 1
for line in range(2,83):
    to_line = raw_to[line].split()
    ll_line = raw_ll[line].split()
    #print to_line[3]
    avg_time_to.append(float(to_line[3].replace(",", "")))
    avg_l1_to.append(float(to_line[4].replace(",", "")))
    avg_llc_to.append(float(to_line[5].replace(",", "")))

    avg_time_ll.append(float(ll_line[3].replace(",", "")))
    avg_l1_ll.append(float(ll_line[4].replace(",", "")))
    avg_llc_ll.append(float(ll_line[5].replace(",", "")))

    if count == 10:
        count = 1
        grid_size = to_line[1].replace(",", "")
        output_to = float(to_line[2].replace(",", ""))
        output_ll = float(ll_line[2].replace(",", ""))
        write_to.write("avg\t"+str(grid_size)+"\t"+str(output_to)+"\t"+str(sum(avg_time_to)/len(avg_time_to))+"\t"+str(sum(avg_l1_to)/len(avg_l1_to))+"\t"+str(sum(avg_llc_to)/len(avg_llc_to))+"\n")
        write_ll.write("avg\t"+str(grid_size)+"\t"+str(output_ll)+"\t"+str(sum(avg_time_ll)/len(avg_time_ll))+"\t"+str(sum(avg_l1_ll)/len(avg_l1_ll))+"\t"+str(sum(avg_llc_ll)/len(avg_llc_ll))+"\n")

    #print to_line
    count += 1
