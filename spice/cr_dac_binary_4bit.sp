* ============================================================================
*  Minimal charge-redistribution DAC: 4-bit plain binary array, one coarse
*  region, reset-to-V_L, top-plate parasitic, DEMUX/S&H with leakage.
*  Same phase scheme as cr_dac_bwa_10bit.sp; intended for reading / first runs.
*  Dialect: ngspice.
* ============================================================================
.param C0=10f  ALPHA=1e-9  CTOT={16*C0}  CP={ALPHA/(1-ALPHA)*CTOT}
.param VLREF=0.375 VUREF=0.5
.param CST=200f RSER=10k ILEAK=1p FR=3.9k TR={1/FR} TSLOT={TR/8}
.param D=9                         ; 4-bit code 0..15  (9 = 1001b)
.param b0={floor(D/1)-2*floor(D/2)}
.param b1={floor(D/2)-2*floor(D/4)}
.param b2={floor(D/4)-2*floor(D/8)}
.param b3={floor(D/8)-2*floor(D/16)}

Vvl vl 0 DC {VLREF}
Vvu vu 0 DC {VUREF}
Vrst  rst  0 PULSE(0 1 0              1n 1n {0.10*TSLOT} {TR})
Vconv conv 0 PULSE(0 1 {0.10*TSLOT+5n} 1n 1n {0.85*TSLOT} {TR})
Vsmp  smp  0 PULSE(0 1 {0.40*TSLOT}    1n 1n {0.50*TSLOT} {TR})
Vb0 nb0 0 DC {b0}
Vb1 nb1 0 DC {b1}
Vb2 nb2 0 DC {b2}
Vb3 nb3 0 DC {b3}
Bc0 c0 0 V = V(conv)*V(nb0)
Bc1 c1 0 V = V(conv)*V(nb1)
Bc2 c2 0 V = V(conv)*V(nb2)
Bc3 c3 0 V = V(conv)*V(nb3)
Bn0 n0 0 V = 1 - V(c0)
Bn1 n1 0 V = 1 - V(c1)
Bn2 n2 0 V = 1 - V(c2)
Bn3 n3 0 V = 1 - V(c3)
.model SW SW(Ron=1k Roff=1T Vt=0.5 Vh=0.05)

* binary-weighted array, top plate = nt
C0x nt bp0 {1*C0}
C1x nt bp1 {2*C0}
C2x nt bp2 {4*C0}
C3x nt bp3 {8*C0}
Cdum nt vl {1*C0}               ; dummy -> C_total = 16 C0, LSB = (VU-VL)/16
SU0 bp0 vu c0 0 SW
SL0 bp0 vl n0 0 SW
SU1 bp1 vu c1 0 SW
SL1 bp1 vl n1 0 SW
SU2 bp2 vu c2 0 SW
SL2 bp2 vl n2 0 SW
SU3 bp3 vu c3 0 SW
SL3 bp3 vl n3 0 SW
Srst nt vl rst 0 SW
Cp   nt 0  {CP}

Sdmx nt nsh smp 0 SW
Rser nsh nst {RSER}
Cst  nst 0 {CST}
Ilk  nst 0 DC {ILEAK}

* expected (ALPHA~0, D=9): V(nt) during conv = 0.375 + 0.125*9/16 = 0.4453125 V
* charge-sharing factor per refresh: CTOT/(CTOT+CST) = 160f/360f = 0.44
.tran {TR/4000} {6*TR}
.control
run
meas tran v_dac find v(nt) at={0.35*TSLOT}
meas tran v_st5 find v(nst) at={4.95*TR}
wrdata cr_dac_4bit_out.txt v(nt) v(nst) v(rst) v(conv) v(smp)
.endc
.end
