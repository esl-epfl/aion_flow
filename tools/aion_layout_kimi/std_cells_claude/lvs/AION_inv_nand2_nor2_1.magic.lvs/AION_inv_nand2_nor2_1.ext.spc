* NGSPICE file created from AION_inv_nand2_nor2_1.ext - technology: ihp-sg13g2

.subckt AION_inv_nand2_nor2_1 I1 I0 I2 O0 VDD VSS
X0 VSS I1 a_46_118# VSS sg13_lv_nmos ad=0.1406p pd=1.12u as=0.2812p ps=2.24u w=0.74u l=0.13u
X1 O0 a_46_118# VSS VSS sg13_lv_nmos ad=0.1406p pd=1.12u as=0.1406p ps=1.12u w=0.74u l=0.13u
X2 VDD I1 a_46_118# VDD sg13_lv_pmos ad=0.2128p pd=1.5u as=0.4256p ps=3u w=1.12u l=0.13u
X3 VSS I0 O0 VSS sg13_lv_nmos ad=0.1406p pd=1.12u as=0.1406p ps=1.12u w=0.74u l=0.13u
X4 a_250_415# a_46_118# VDD VDD sg13_lv_pmos ad=0.2128p pd=1.5u as=0.2128p ps=1.5u w=1.12u l=0.13u
X5 O0 I2 VSS VSS sg13_lv_nmos ad=0.2812p pd=2.24u as=0.1406p ps=1.12u w=0.74u l=0.13u
X6 a_352_415# I0 a_250_415# VDD sg13_lv_pmos ad=0.2128p pd=1.5u as=0.2128p ps=1.5u w=1.12u l=0.13u
X7 O0 I2 a_352_415# VDD sg13_lv_pmos ad=0.4256p pd=3u as=0.2128p ps=1.5u w=1.12u l=0.13u
.ends

