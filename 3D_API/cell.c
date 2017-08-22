#include<stdio.h>
#include<stdlib.h>
#include<string.h> 

#define MAX_LAYER_NUM 10 ///supporting up to 10 chip stacking
#define GRID_SIZE 512
#define MAX_CHAR_SIZE 100 // input file format
#define MAX_GROUP_NUM 50

#define TULSA_X 0.02184   //default chip sizes
#define TULSA_Y 0.02184
#define PHI7250_X 0.0315
#define PHI7250_Y 0.0205
#define E52667V4_X 0.012634
#define E52667V4_Y 0.014172
     
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
	FILE *fp;
	char *fname; // input 3-D stacking layout file
	char s1[MAX_CHAR_SIZE];
	char s2[MAX_CHAR_SIZE];
	char *chip_name;  
	int i, j, w;
	int x, y;
	float chip_x, chip_y;
	float chip_xlen, chip_ylen;
	int layer;
	//int rotate, freq; 

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

	fp = fopen(fname, "r");
	if(fp == NULL){
		printf("%s cannot read\n", fname);
		return -1;
	}

	//Find longest (X or Y-) lenggh of 3-D chip-stacking (including null block). 
	while(fgets(s1,MAX_CHAR_SIZE, fp) != NULL){
		for(i = 0; i < MAX_CHAR_SIZE; i++) s2[i] = s1[i];
		chip_name = strtok(s2, " ");
		if(!strcmp(chip_name, "tulsa")){
			chip_xlen = TULSA_X;
			chip_ylen = TULSA_Y;
		}else if(!strcmp(chip_name, "phi7250")){
			chip_xlen = PHI7250_X;
			chip_ylen = PHI7250_Y;
		}else if(!strcmp(chip_name, "e5-2667v4")){
			chip_xlen = E52667V4_X;
			chip_ylen = E52667V4_Y;
		}else{
			fprintf(stderr, "invalid chip name in input file '%s'", fname);
			exit(1);
		}
		layer = atoi(strtok(NULL, " "));
		chip_x = atof(strtok(NULL, " "));
		chip_y = atof(strtok(NULL, " "));
		//freq = atoi(strtok(NULL, " "));
		//rotate = atoi(strtok(NULL, " "));

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
	x_left = x_right = y_top = y_bottom = -1;
	while(fgets(s1, MAX_CHAR_SIZE, fp) != NULL){
		for(i = 0; i < MAX_CHAR_SIZE; i++)
			s2[i] = s1[i];
		chip_name = strtok(s2, " ");
		if(!strcmp(chip_name, "tulsa")){
			chip_xlen = TULSA_X;
			chip_ylen = TULSA_Y;
		}else if(!strcmp(chip_name, "phi7250")){
			chip_xlen = PHI7250_X;
			chip_ylen = PHI7250_Y;
		}else if(!strcmp(chip_name, "e5-2667v4")){
			chip_xlen = E52667V4_X;
			chip_ylen = E52667V4_Y;
		}else{
			fprintf(stderr, "invalid chip name in input file '%s'", fname);
			exit(1);
		}
		layer = atoi(strtok(NULL, " "));
		chip_x = atof(strtok(NULL, " "));
		chip_y = atof(strtok(NULL, " "));
		//freq = atoi(strtok(NULL, " "));
		//rotate = atoi(strtok(NULL, " "));
	
		x_left = chip_x / cell;
		x_right = (chip_x+chip_xlen) /cell;
		y_top = chip_y / cell;
		y_bottom = (chip_y+chip_ylen) /cell;
		for(i = x_left; i < x_right; i++)
			for(j = y_top; j < y_bottom; j++)		
				grid_group_label[layer][i][j] = 1; 		
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
	for(layer = 1; layer <= layer_num; layer++){//layer starts from 1
		for(group = 2; group < MAX_GROUP_NUM; group++){//null group stars from 2
			//this judgement is strange, if those 2 values are 0, that means there are 0 * 0 blocks.
			//if used, 2 values would be non-zero.   
			if(xlen_in_group[layer][group] != 0 &&
				 ylen_in_group[layer][group] != 0) 
				 printf("%d NULL%d %f %f %f %f\n",layer, group, xlen_in_group[layer][group], ylen_in_group[layer][group], x_in_group[layer][group], y_in_group[layer][group]);		
		}
	}	
	return 0;
}


