* ============================================================================
*  Charge-redistribution bias DAC  --  10-bit split array (5 LSB + C_A + 5 MSB)
*  + coarse reference pair (V_L, V_U) + reset + DEMUX/S&H + leakage + refresh
*  Topology after Vliex et al., IEEE SSC-L 2020, Fig. 2 / Fig. 3(b).
*  Ideal switches, behavioral timing.  Dialect: ngspice (LTspice notes at end).
*  Companion: docs/figures/cr_dac_topology.png, model/bias_dac_v2.py
* ============================================================================
*  Node names
*    vu, vl   : coarse references (upper / lower tap of the 125-mV ladder)
*    na       : LSB sub-array top plate  (node A)
*    nb       : MSB sub-array top plate  = DAC output (node B)
*    bpX      : bottom plate of capacitor X
*    nsh, nst : after DEMUX switch / on storage capacitor (channel k)
*    rst, conv, smp : phase signals (1 V = active)
* ----------------------------------------------------------------------------

* ---------------- user parameters -------------------------------------------
.param C0     = 5f          ; unit capacitor                       [Assume]
.param CA     = {C0*32/31}  ; attenuation cap, classic split-array value
.param ALPHA  = 1e-9        ; parasitic ratio at node B: ~0 -> ideal; 0.064 -> Fig. 9(a) [Paper-read]
.param CBEFF  = {33*C0}     ; effective cap seen at node B (31 + series(C_A, 32)) ~ 33 C0
.param CP     = {ALPHA/(1-ALPHA)*CBEFF}
.param VLREF  = 0.375       ; V_L = ladder tap 3   (paper Fig. 9 example region)
.param VUREF  = 0.500       ; V_U = ladder tap 4   (span 125 mV);  use 0.625 for the 250-mV intermediate span
.param CST    = 1p          ; storage cap per channel               [Assume]
.param RSER   = 10k         ; series R in S&H path                  [Assume]
.param ILEAK  = 1p          ; leakage on storage cap (paper: pA design target)  [Assume]
.param FR     = 3.9k        ; channel refresh rate (paper sweet spot); try 390k
.param NCH    = 8           ; channels sharing the DAC
.param TR     = {1/FR}      ; channel refresh period
.param TSLOT  = {TR/NCH}    ; conversion slot per channel
.param D      = 1023        ; 10-bit fine code 0..1023

* bit extraction  b_i = floor(D/2^i) - 2*floor(D/2^(i+1))
.param b0={floor(D/1)  -2*floor(D/2)}
.param b1={floor(D/2)  -2*floor(D/4)}
.param b2={floor(D/4)  -2*floor(D/8)}
.param b3={floor(D/8)  -2*floor(D/16)}
.param b4={floor(D/16) -2*floor(D/32)}
.param b5={floor(D/32) -2*floor(D/64)}
.param b6={floor(D/64) -2*floor(D/128)}
.param b7={floor(D/128)-2*floor(D/256)}
.param b8={floor(D/256)-2*floor(D/512)}
.param b9={floor(D/512)-2*floor(D/1024)}

* ---------------- references (external, ideal) ------------------------------
Vvl vl 0 DC {VLREF}
Vvu vu 0 DC {VUREF}

* ---------------- phase generator (one channel shown, period = T_R) ---------
* reset  : first 10 % of the slot            (top plates + all bottom plates to V_L)
* conv   : 10 % .. 95 % of the slot          (selected bottom plates to V_U, top plates float)
* smp    : 40 % .. 90 % of the slot          (DEMUX closes: charge sharing into C_storage)
Vrst  rst  0 PULSE(0 1 0              1n 1n {0.10*TSLOT} {TR})
Vconv conv 0 PULSE(0 1 {0.10*TSLOT+5n} 1n 1n {0.85*TSLOT} {TR})
Vsmp  smp  0 PULSE(0 1 {0.40*TSLOT}    1n 1n {0.50*TSLOT} {TR})

* ---------------- code bits as voltages (0 / 1 V) ---------------------------
Vb0 nb0 0 DC {b0}
Vb1 nb1 0 DC {b1}
Vb2 nb2 0 DC {b2}
Vb3 nb3 0 DC {b3}
Vb4 nb4 0 DC {b4}
Vb5 nb5 0 DC {b5}
Vb6 nb6 0 DC {b6}
Vb7 nb7 0 DC {b7}
Vb8 nb8 0 DC {b8}
Vb9 nb9 0 DC {b9}

* switch controls: to V_U when (conv AND bit), else to V_L
Bc0 c0 0 V = V(conv)*V(nb0)
Bc1 c1 0 V = V(conv)*V(nb1)
Bc2 c2 0 V = V(conv)*V(nb2)
Bc3 c3 0 V = V(conv)*V(nb3)
Bc4 c4 0 V = V(conv)*V(nb4)
Bc5 c5 0 V = V(conv)*V(nb5)
Bc6 c6 0 V = V(conv)*V(nb6)
Bc7 c7 0 V = V(conv)*V(nb7)
Bc8 c8 0 V = V(conv)*V(nb8)
Bc9 c9 0 V = V(conv)*V(nb9)
Bn0 n0 0 V = 1 - V(c0)
Bn1 n1 0 V = 1 - V(c1)
Bn2 n2 0 V = 1 - V(c2)
Bn3 n3 0 V = 1 - V(c3)
Bn4 n4 0 V = 1 - V(c4)
Bn5 n5 0 V = 1 - V(c5)
Bn6 n6 0 V = 1 - V(c6)
Bn7 n7 0 V = 1 - V(c7)
Bn8 n8 0 V = 1 - V(c8)
Bn9 n9 0 V = 1 - V(c9)

.model SW SW(Ron=1k Roff=1T Vt=0.5 Vh=0.05)

* ---------------- LSB sub-array: node A ------------------------------------
CL0 na bp0 {1*C0}
CL1 na bp1 {2*C0}
CL2 na bp2 {4*C0}
CL3 na bp3 {8*C0}
CL4 na bp4 {16*C0}
Cdum na vl {1*C0}          ; dummy unit, always at V_L  -> LSB array total = 32 C0
SU0 bp0 vu c0 0 SW
SL0 bp0 vl n0 0 SW
SU1 bp1 vu c1 0 SW
SL1 bp1 vl n1 0 SW
SU2 bp2 vu c2 0 SW
SL2 bp2 vl n2 0 SW
SU3 bp3 vu c3 0 SW
SL3 bp3 vl n3 0 SW
SU4 bp4 vu c4 0 SW
SL4 bp4 vl n4 0 SW
SrstA na vl rst 0 SW       ; node A reset

* ---------------- attenuation capacitor --------------------------------------
CAtt na nb {CA}

* ---------------- MSB sub-array: node B (DAC output) -------------------------
CM0 nb bp5 {1*C0}
CM1 nb bp6 {2*C0}
CM2 nb bp7 {4*C0}
CM3 nb bp8 {8*C0}
CM4 nb bp9 {16*C0}
SU5 bp5 vu c5 0 SW
SL5 bp5 vl n5 0 SW
SU6 bp6 vu c6 0 SW
SL6 bp6 vl n6 0 SW
SU7 bp7 vu c7 0 SW
SL7 bp7 vl n7 0 SW
SU8 bp8 vu c8 0 SW
SL8 bp8 vl n8 0 SW
SU9 bp9 vu c9 0 SW
SL9 bp9 vl n9 0 SW
SrstB nb vl rst 0 SW       ; node B reset to V_L: this is what pins the region start (see docs 4.5)
Cp   nb 0  {CP}            ; top-plate parasitic -> region gain (1 - ALPHA)

* ---------------- DEMUX + S&H channel k --------------------------------------
Sdmx nb  nsh smp 0 SW      ; DEMUX (1 of 8) -- no output buffer
Rser nsh nst {RSER}
Cst  nst 0   {CST}
Ilk  nst 0   DC {ILEAK}    ; leakage discharging the storage cap
* bond wire + electrode (paper Fig. 2); inductor omitted to keep the time step large
Rbw  nst nq  1
Cq   nq  0   100f          ; C_electrode  [Assume]

* ---------------- analysis ---------------------------------------------------
* expected (ideal, ALPHA~0, D=1023): V(nb) during conv = VLREF + (VUREF-VLREF)*1023/1024 = 0.499878 V
* expected (ALPHA=0.064, D=1023)   : V(nb) = 0.375 + 0.125*0.936*1023/1024 = 0.491886 V  (8.0 mV short of 0.5 V)
* storage cap after n refreshes    : V_st -> V(nb) with per-refresh factor CBEFF/(CBEFF+CST) ~ 0.14 here
*                                    (CBEFF = 33*5 fF = 165 fF << CST = 1 pF; raise C0 or lower CST to converge faster)
* leakage droop per period         : ILEAK*TR/CST = 1p*256u/1p = 256 uV at 3.9 kHz ; 2.6 uV at 390 kHz
.tran {TR/4000} {6*TR}
.option method=gear reltol=1e-4

.control
run
meas tran v_dac_conv   find v(nb)  at={0.35*TSLOT}
meas tran v_st_after1  find v(nst) at={0.95*TR}
meas tran v_st_after5  find v(nst) at={4.95*TR}
meas tran v_st_before6 find v(nst) at={5.0*TR-1n}
wrdata cr_dac_bwa_out.txt v(nb) v(na) v(nst) v(rst) v(conv) v(smp)
* plot v(nb) v(nst)          ; uncomment in interactive ngspice
.endc

* ---------------- optional: transfer-curve sweep over the fine code -------
* (interactive ngspice)  foreach code 0 128 256 384 512 640 768 896 1023
*   alterparam D=$code
*   reset
*   run
*   meas tran vout find v(nb) at={0.35*TSLOT}
* end

* ---------------- LTspice notes ---------------------------------------------
* - remove the .control/.endc block and use  .meas tran v_dac find V(nb) at=...
* - .param with floor() and the B-source syntax  V = V(conv)*V(nb0)  are accepted
* - switch model:  .model SW SW(Ron=1k Roff=1T Vt=0.5 Vh=0.05)  is accepted as is
.end
