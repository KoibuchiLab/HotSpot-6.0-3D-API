#include<stdio.h>
#include<stdlib.h>
#include<string.h> 

#define MAX_LAYER_NUM 20 ///supporting up to 20 chip stacking
#ifndef GRID_SIZE
#define GRID_SIZE 2048//8192
#endif
#define OUTPUT_GRID_SIZE 64
#define MAX_CHAR_SIZE 100 // input file format
#define MAX_GROUP_NUM 50

#define TULSA_X 0.02184   //default chip sizes
#define TULSA_Y 0.02184
#define PHI7250_X 0.0315
#define PHI7250_Y 0.0205
#define E52667V4_X 0.012634
#define E52667V4_Y 0.014172
#define BASE1_X 0.016
#define BASE1_Y 0.016
#define BASE2_X 0.013
#define BASE2_Y 0.013

     
static int grid_group_label[MAX_LAYER_NUM][GRID_SIZE][GRID_SIZE];
//gird_group_label shows, what group the grid belong.
//if this label is 1, the grid belong chips.
//if this label is 0, the grid belong null and this hasn't be detected
//we will find null square, and divided into some groups, then those label would be 2, 3, ...   


// for print debugging purpose
void graph(void){
	int x, y, layer;
	int grid_interval = 25;
	for(layer = 1; layer < MAX_LAYER_NUM; layer++){ 
		for(y = 0; y < GRID_SIZE; y += grid_interval){
			for(x = 0; x < GRID_SIZE; x += grid_interval){
				printf("%2d ", grid_group_label[layer][x][y]);
			}
			printf("\n");	
		}
		printf("\n");
	}
}

int main(int argc, char **argv){
	
	//printf("start cell\n");
	FILE *fp, *file, *outfile;
	char *fname; // input 3-D stacking layout file
	char s1[MAX_CHAR_SIZE];
	char s2[MAX_CHAR_SIZE];
	char *chip_name;  
	int i, j, w;
	int x, y;
	float chip_x, chip_y;
	float chip_xlen, chip_ylen;
	int layer;
	int rotate;
	char *freq; 

	if (argc != 2) {
		fprintf(stderr,"Usage: %s <input file (.dat)>\n", argv[0]);
		exit(1);
	}

	fname = argv[1];

	float system_size = 0; // system X or Y length of 3D-chip stacking.
	//float h = 0.02184; //default Xeon Tulsa chip length (m)
	float cell = -1; // length of each grid size (m)

	for(w = 0; w < MAX_LAYER_NUM; w++)
		for(i = 0; i < GRID_SIZE; i++)
			for(j = 0; j < GRID_SIZE; j++)
				grid_group_label[w][i][j] = 0;			

	//for just reading input file 
	fp = fopen(fname, "r");
	if(fp == NULL){
		printf("%s cannot read\n", fname);
		return -1;
	}

	//for holding chip coodinate 
	file = fopen("detailed.tmp", "w");
	if(file == NULL){
		fprintf(stderr, "error: cannot open file 'for_detailed.tmp'");
		exit(1);
	}
	

	//Find longest (X or Y-) lenggh of 3-D chip-stacking (including null block). 
	while(fgets(s1,MAX_CHAR_SIZE, fp) != NULL){
		for(i = 0; i < MAX_CHAR_SIZE; i++) s2[i] = s1[i];
		chip_name = strtok(s2, " ");
		layer = atoi(strtok(NULL, " "));
		chip_x = atof(strtok(NULL, " "));
		chip_y = atof(strtok(NULL, " "));
		strtok(NULL, " ");
		//freq = atoi(strtok(NULL, " "));
		rotate = atoi(strtok(NULL, " "));
		if(strstr(chip_name, "tulsa") != NULL){
			if(rotate == 0 || rotate == 180){
				chip_xlen = TULSA_X;
				chip_ylen = TULSA_Y;
			}else if(rotate == 90 || rotate == 270){
				chip_xlen = TULSA_Y;
				chip_ylen = TULSA_X;
			}else{
				fprintf(stderr, "invalid rotation in input file '%s'", fname);
				exit(1);
			}
		}else if(strstr(chip_name, "phi7250") != NULL){
			if(rotate == 0 || rotate == 180){
				chip_xlen = PHI7250_X;
				chip_ylen = PHI7250_Y;
			}else if(rotate == 90 || rotate == 270){
				chip_xlen = PHI7250_Y;
				chip_ylen = PHI7250_X;
			}else{
				fprintf(stderr, "invalid rotation in input file '%s'", fname);
				exit(1);
			}
		}else if(strstr(chip_name, "e5-2667v4") != NULL){
			if(rotate == 0 || rotate == 180){
				chip_xlen = E52667V4_X;
				chip_ylen = E52667V4_Y;
			}else if(rotate == 90 || rotate == 270){
				chip_xlen = E52667V4_Y;
				chip_ylen = E52667V4_X;
			}else{
				fprintf(stderr, "invalid rotation in input file '%s'", fname);
				exit(1);
			}
		}else if(strstr(chip_name, "base1") != NULL){
			if(rotate == 0 || rotate == 180){
				chip_xlen = BASE1_X;
				chip_ylen = BASE1_Y;
			}else if(rotate == 90 || rotate == 270){
				chip_xlen = BASE1_Y;
				chip_ylen = BASE1_X;
			}else{
				fprintf(stderr, "invalid rotation in input file '%s'", fname);
				exit(1);
			}			
		}else if(strstr(chip_name, "base2") != NULL){
			if(rotate == 0 || rotate == 180){
				chip_xlen = BASE2_X;
				chip_ylen = BASE2_Y;
			}else if(rotate == 90 || rotate == 270){
				chip_xlen = BASE2_Y;
				chip_ylen = BASE2_X;
			}else{
				fprintf(stderr, "invalid rotation in input file '%s'", fname);
				exit(1);
			}
		}else if(strstr(chip_name, "null") != NULL){
			chip_xlen = 0.00001;
			chip_ylen = 0.00001;
		}else{
			fprintf(stderr, "invalid rotation in input file '%s'", fname);
			exit(1);
		}

		//create the SQUARE that include all chips, the length would be system_size 
		if(chip_x+chip_xlen > system_size)
			system_size = chip_x+chip_xlen;
		if(chip_y+chip_ylen > system_size)
			system_size = chip_y+chip_ylen; 		
	}	
	cell = system_size /(float)GRID_SIZE;

	fclose(fp);
	fp = fopen(fname, "r");
	if(fp == NULL){
		printf("%s cannot read\n", fname);
		return -1;
	}

	int x_left, x_right, y_top, y_bottom;
	int rank = 0; 
	x_left = x_right = y_top = y_bottom = -1;
	while(fgets(s1, MAX_CHAR_SIZE, fp) != NULL){
		for(i = 0; i < MAX_CHAR_SIZE; i++)
			s2[i] = s1[i];
		chip_name = strtok(s2, " ");
		layer = atoi(strtok(NULL, " "));
		chip_x = atof(strtok(NULL, " "));
		chip_y = atof(strtok(NULL, " "));
		freq = strtok(NULL, " ");
		rotate = atoi(strtok(NULL, " "));
		rank = atoi(strtok(NULL, " "));
		
		if(strstr(chip_name, "tulsa")!= NULL){
			if(rotate == 0 || rotate == 180){
				chip_xlen = TULSA_X;
				chip_ylen = TULSA_Y;
			}else if(rotate == 90 || rotate == 270){
				chip_xlen = TULSA_Y;
				chip_ylen = TULSA_X;
			}else{
				fprintf(stderr, "invalid rotation in input file '%s'", fname);
				exit(1);
			}
		}else if(strstr(chip_name, "phi7250")!= NULL){
			if(rotate == 0 || rotate == 180){
				chip_xlen = PHI7250_X;
				chip_ylen = PHI7250_Y;
			}else if(rotate == 90 || rotate == 270){
				chip_xlen = PHI7250_Y;
				chip_ylen = PHI7250_X;
			}else{
				fprintf(stderr, "invalid rotation in input file '%s'", fname);
				exit(1);
			}
		}else if(strstr(chip_name, "e5-2667v4")!= NULL){
			if(rotate == 0 || rotate == 180){
				chip_xlen = E52667V4_X;
				chip_ylen = E52667V4_Y;
			}else if(rotate == 90 || rotate == 270){
				chip_xlen = E52667V4_Y;
				chip_ylen = E52667V4_X;
			}else{
				fprintf(stderr, "invalid rotation in input file '%s'", fname);
				exit(1);
			}
		}else if(strstr(chip_name, "base1") != NULL){
			if(rotate == 0 || rotate == 180){
				chip_xlen = BASE1_X;
				chip_ylen = BASE1_Y;
			}else if(rotate == 90 || rotate == 270){
				chip_xlen = BASE1_Y;
				chip_ylen = BASE1_X;
			}else{
				fprintf(stderr, "invalid rotation in input file '%s'", fname);
				exit(1);
			}			
		}else if(strstr(chip_name, "base2") != NULL){
			if(rotate == 0 || rotate == 180){
				chip_xlen = BASE2_X;
				chip_ylen = BASE2_Y;
			}else if(rotate == 90 || rotate == 270){
				chip_xlen = BASE2_Y;
				chip_ylen = BASE2_X;
			}else{
				fprintf(stderr, "invalid rotation in input file '%s'", fname);
				exit(1);
			}			
		}else if(strstr(chip_name, "null") != NULL){
			chip_xlen = 0.00001;
			chip_ylen = 0.00001;
		}else{
			fprintf(stderr, "invalid rotation in input file '%s'", fname);
			exit(1);
		}
		x_left = chip_x / cell;
		x_right = (chip_x+chip_xlen) /cell;
		y_top = chip_y / cell;
		y_bottom = (chip_y+chip_ylen) /cell;
		for(i = x_left; i < x_right; i++)
			for(j = y_top; j < y_bottom; j++)		
				grid_group_label[layer][i][j] = 1;

		//for holding chip coordinates at 64 * 64(OUTPUT_GRID_SIZE)
		x_left = (float) x_left * OUTPUT_GRID_SIZE / GRID_SIZE;
		x_right = (float) x_right * OUTPUT_GRID_SIZE / GRID_SIZE;
		y_top = (float) y_top * OUTPUT_GRID_SIZE / GRID_SIZE;
		y_bottom = (float) y_bottom * OUTPUT_GRID_SIZE / GRID_SIZE;
		fprintf(file,"%s %d %d %d %d %d %f %f %s %d %d\n", chip_name, layer, x_left, x_right, OUTPUT_GRID_SIZE - y_bottom, OUTPUT_GRID_SIZE - y_top, chip_x, chip_y, freq, rotate, rank);
		 		
	}
	fclose(fp);
	
	int len_of_upper, len_of_middle, break_flag;
	break_flag = 0;
	int group = 2;
    //this declarement is very verbose
	//*_in_group means the coordinate, when each layer, group
	//*len_in_group means the length, when each layer, group
	//so, unused arrays are always ZERO.     
	float x_in_group[MAX_LAYER_NUM][MAX_GROUP_NUM];
	float y_in_group[MAX_LAYER_NUM][MAX_GROUP_NUM];
	float xlen_in_group[MAX_LAYER_NUM][MAX_GROUP_NUM];
	float ylen_in_group[MAX_LAYER_NUM][MAX_GROUP_NUM];
	for(i = 0; i < MAX_LAYER_NUM; i++)
		for(j = 0; j < MAX_GROUP_NUM; j++){
			x_in_group[i][j] = 0;
			y_in_group[i][j] = 0;
			xlen_in_group[i][j] = 0;
			ylen_in_group[i][j] = 0;

		}
	int layer_num = layer;
	int tmp_x, tmp_y;	
			

//gird_group_label shows, what group the grid belong.
//if this label is 1, the grid belong chips.
//if this label is 0, the grid belong null and this hasn't be detected
//we will find null square, and divided into some groups, then those label would be 2, 3, ...
//if label, grid_group_label(layer,x,y)==0, then serach the null square from the point.     
	for(layer = 1; layer <= layer_num; layer++){ 
		for(y = 0; y < GRID_SIZE; y++){
			for(x = 0; x < GRID_SIZE; x++){
				if(grid_group_label[layer][x][y] == 0){
					len_of_upper = 0;
					for(tmp_x = x; tmp_x < GRID_SIZE; tmp_x++){
						if(grid_group_label[layer][tmp_x][y] == 0){
							len_of_upper++;
						}else{
							break;
						}
					}
					break_flag = 0;
					for(tmp_y = y + 1; tmp_y < GRID_SIZE; tmp_y++){
						len_of_middle = 0;
						for(tmp_x = x; tmp_x < x + len_of_upper; tmp_x++){
							if(tmp_y == GRID_SIZE-1 && tmp_x == x + len_of_upper-1 && grid_group_label[layer][tmp_x][tmp_y] == 0){
								break_flag = 1;
								
								//square (x,  x+len_of_upper, y, tmp_y) would be non-zero 
								for(i = x; i < x + len_of_upper; i++){
									for(j = y; j < tmp_y; j++){
											grid_group_label[layer][i][j] = group;
											x_in_group[layer][group] = x * cell;
											y_in_group[layer][group] = y * cell;
											xlen_in_group[layer][group] = len_of_upper * cell;
											ylen_in_group[layer][group] = (tmp_y - y+1) * cell;
										}
								}
								//until here
								break;
							}	
				    		if(grid_group_label[layer][tmp_x][tmp_y] == 0){
								len_of_middle++;
							}else{
								if(len_of_middle == len_of_upper){
									break;
								}else{
									break_flag = 1;
									//square (x,  x+len_of_upper, y, tmp_y) would be non-zero 
									for(i = x; i < x + len_of_upper; i++){
										for(j = y; j < tmp_y; j++){
											grid_group_label[layer][i][j] = group;
											x_in_group[layer][group] = x * cell;
											y_in_group[layer][group] = y * cell;
											xlen_in_group[layer][group] = len_of_upper * cell;
											ylen_in_group[layer][group] = (tmp_y - y) * cell;
										}
									}
									//until here
									break;
								}
							}
						}
						if(break_flag == 1){
							group++; 
							break;
						}
					}
				}
			}
		}
	}

	//graph();
	
	outfile = fopen("null_LL.data","w+");
	for(layer = 1; layer <= layer_num; layer++){//layer starts from 1
		for(group = 2; group < MAX_GROUP_NUM; group++){//null group stars from 2
			//this judgement is strange, if those 2 values are 0, that means there are 0 * 0 blocks.
			//if used, 2 values would be non-zero.   
			if(xlen_in_group[layer][group] != 0 &&
				 ylen_in_group[layer][group] != 0) 
				 fprintf(outfile,"%d NULL%d %0.8f %0.8f %0.8f %0.8f\n",layer, group, xlen_in_group[layer][group], ylen_in_group[layer][group], x_in_group[layer][group], y_in_group[layer][group]);		
		}
	}	
	return 0;
}


