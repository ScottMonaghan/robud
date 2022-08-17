# Ro-Bud - Lovable, Accessible, Autonomous Companion
<img src="./data/images/Ro-Bud-concept-render.jpeg" alt="Ro-bud" width=600 />  

## Table of Contents
 * [Summary](#summary)
 * [Description](#description)
 * [Pre-Alpha Build Instructions](#pre-alpha-build-instructions)
   * [Parts Reference](#parts-reference)
   * [Head Assembly](#head-assembly)
 * [Original Project Announcement Videos](#original-project-announcement-videos)
   * [Part 1](#part-1)
   * [Part 2](#part-2)
   * [Part 3](#part-3)
   * [Part 4](#part-4)
## Summary
The Ro-Bud project seeks to create a companion bot that is lovable, accessible to all, and autonomous.  

[Return to Table of Contents](#table-of-contents)

## Description
Challenge: Despite decades of fictional depiction through popular culture, as of 2021, robotic companion bots that even come close to those of popular imagination are not available at scale.

While there have been impressive private for-profit attempts at releasing relatively advanced consumer companion bots, specifically Jibo and Anki Vector, these endeavors ultimately proved commercially unviable, forcing the companies to fold, and effectively removing these wonderfully engineered robots from either availability or full operability (as they were dependent on proprietary services provided by their now-defunct companies).

The Ro-Bud project is an attempt to pick up where Jibo and Ankni left off, and fulfil the dream of providing a consumer robot that is:
1. LOVEABLE - Feels just like a family pet
2. ACCESSIBLE - Can be built by anyone following project instructions with readily available parts with a cost at or under $500
3. AUTONOMOUS - Has it's own goals.  

[Return to Table of Contents](#table-of-contents)

# Alpha Build Instructions
**NOTE: The following build instructions are in-progress and not yet complete**  
Last updated 17-August 2022

<img src="./data/images/build-instructions/IMG_4106.jpg" alt="Pre-Alpha Ro-Bud Build" width=600 />

**Documentation To-Do**
 * [x] Add 3d-printable models
 * [ ] Jetson Wifi Module Install
 * [ ] SD Card Flashing
 * [x] Head Assembly  
 * [ ] Remote VM setup
 * [ ] Remote Operation Instructions

[Return to Table of Contents](#table-of-contents)

## Master Parts Reference
 * A. horizontal braces [stl](./data/stl/robud-horizontal-brace.stl)
 * B. 3-hole fastener [stl](./data/stl/robud-3-hole-fastener.stl)
 * C. 2x8mm round-head self-tapping screws https://www.amazon.com/gp/product/B07NT5288W  
 * D. 2x8mm pan-head-with-washer self-tapping screws https://www.amazon.com/gp/product/B07NTGRFBF  
 * E. BNO055 orientation sensor https://www.adafruit.com/product/4646, https://www.digikey.com/en/products/detail/adafruit-industries-llc/4646/12609996
 * F. SainSmart IMX219 Camera Module https://www.amazon.com/gp/product/B07VFFRX4C  
 * G. VL53L0X time-of-flight distance sensor https://www.adafruit.com/product/3317  
 * H. 1-hole 2mm screw fastener [stl](./data/stl/robud-1-hole-fastener.stl)
 * I. 300mm 15-pin camera ribbon cable https://www.adafruit.com/product/1648
 * J. 100mm Stemma QT JST SH 4-pin cable https://www.adafruit.com/product/4210
 * K. display fastener [stl](./data/stl/robud-display-fastener.stl)
 * L. servo adapter [stl](./data/stl/robud-servo-adapter.stl)
 * M. head barrel wall [stl](./data/stl/robud-head-barrel-wall.stl)
 * N. head shaft adapter [stl](./data/stl/robud-head-shaft-adapter.stl)
 * O. bearing https://www.amazon.com/gp/product/B07S1B3MS6  
 * Q. MG90S 9G micro servo https://www.amazon.com/gp/product/B07F7VJQL5  
 * R. 7in display https://www.adafruit.com/product/1934  
 * S. 250mm 40pin display ribbon cable https://www.amazon.com/gp/product/B00N426GJA  
 * T. mono enclosed speaker - 3W 4 Ohm https://www.adafruit.com/product/3351  
 * U. head L bracket [stl](./data/stl/robud-head-L-bracket.stl)
 * V. servo horn (included with servo(Q))
 * W. servo screw (included with servo(Q))
 * CC. SparkFun Qwiic SHIM for Raspberry Pi https://www.sparkfun.com/products/15794
 * DD. Stacking Header for Pi A+/B+/Pi 2/Pi 3 - 2x20 Extra Tall Header https://www.adafruit.com/product/1979
 * EE. Adafruit DC & Stepper Motor Bonnet for Raspberry Pi https://www.adafruit.com/product/4280
 * FF. Break-away 0.1" male header https://www.adafruit.com/product/392
 * GG. Male/Male Jumper Wires - 20 x 6" (150mm) https://www.adafruit.com/product/1957
 * HH. Female/Female Jumper Wires - 20 x 6" (150mm)Female/Female Jumper Wires - 20 x 6" (150mm)
 * II. Heat shrink tubing https://www.adafruit.com/product/1649
 * JJ. 3.5mm (1/8") Stereo Audio Plug Terminal Block https://www.adafruit.com/product/2790
 * KK. Rocker toggle switch (comes with chassis kit)
 * LL. Servo Tester https://www.amazon.com/gp/product/B07TQSKLBK
 * MM. PCA9685 16 Channel 12 Bit PWM Servo Driver https://www.amazon.com/gp/product/B07RMTN4NZ
 * NN. Baseus Power Bank, 65W 20000mAh Laptop Portable Charger https://www.amazon.com/gp/product/B08THCNNCS
 * OO. x2 USB-A Male Plug to 5-pin Terminal Block https://www.amazon.com/gp/product/B07H53X194 (2-pack), https://www.digikey.com/en/products/detail/adafruit-industries-llc/3628/7931507 (1-pack)
 * PP. x2 Stacking Header for Pi https://www.adafruit.com/product/1979, https://www.digikey.com/en/products/detail/adafruit-industries-llc/1979/6238003, https://www.amazon.com/gp/product/B071XCHZNB/(4 pack)
 * QQ. M2.5 brass stand-off kit https://www.amazon.com/gp/product/B075K3QBMX/ (or equivalent)
 * RR. 22AWG Silicone Hook Up Wire (stranded) https://www.amazon.com/gp/product/B07T4SYVYG/ (or equivalent, you want not-too-stiff wire than can handle 4 amps)
 * SS. STEMMA QT / Qwiic JST SH 4-Pin Cable - 400mm long https://www.adafruit.com/product/5385, https://www.digikey.com/en/products/detail/adafruit-industries-llc/5385/16546436
 * TT. Heat Shrink Tubing https://www.amazon.com/gp/product/B01MFA3OFA (can be subbed with electrical tape, or equivalent)
 

[Return to Table of Contents](#table-of-contents)
 
## Head Assembly
<img src="./data/images/build-instructions/IMG_3664.jpg" alt="Head Assembly Step 1" width=600 />
<img src="./data/images/build-instructions/IMG_3666.jpg" alt="Head Assembly Step 1" width=600 />

**Full list of Head Assembly Parts**
   * 3d Printed Parts (Ender 3 settings - PLA, Raft recommended, defaults otherwise) 
     * x4 A. horizontal braces [stl](./data/stl/robud-horizontal-brace.stl)
     * x3 B. 3-hole fastener  [stl](./data/stl/robud-3-hole-fastener.stl)
     * x2 H. 1-hole 2mm screw fastener [stl](./data/stl/robud-1-hole-fastener.stl)
     * x4 K. display fastener [stl](./data/stl/robud-display-fastener.stl)
     * x1 L. servo adapter [stl](./data/stl/robud-servo-adapter.stl)
     * x2 M. head barrel wall [stl](./data/stl/robud-head-barrel-wall.stl)
     * x1 N. head shaft adapter [stl](./data/stl/robud-head-shaft-adapter.stl)
     * x2 U. head L bracket [stl](./data/stl/robud-head-L-bracket.stl)
   
   * Adafruit (recommend sourcing from DigiKey for best US price/shipping)
     * x1 E. BNO055 orientation sensor https://www.adafruit.com/product/4646, https://www.digikey.com/en/products/detail/adafruit-industries-llc/4646/12609996 (often out of stock due to chip shortage. Check DigiKey, Adafruit, Mouser & Amazon)
     * x1 G. VL53L0X time-of-flight distance sensor https://www.adafruit.com/product/3317 
     * x1 I. 300mm 15-pin camera ribbon cable https://www.adafruit.com/product/1648
     * x1 J. 100mm Stemma QT JST SH 4-pin cable https://www.adafruit.com/product/4210
     * x1 R. 7in display https://www.adafruit.com/product/1934 
     * x1 T. mono enclosed speaker - 3W 4 Ohm https://www.adafruit.com/product/3351  

   * Amazon
     * x7 C. 2x8mm round-head self-tapping screws https://www.amazon.com/gp/product/B07NT5288W  
     * x20 D. 2x8mm pan-head-with-washer self-tapping screws https://www.amazon.com/gp/product/B07NTGRFBF 
     * x1 F. SainSmart IMX219 Camera Module https://www.amazon.com/gp/product/B07VFFRX4C  
     * x1 O. bearing https://www.amazon.com/gp/product/B07S1B3MS6 
     * x1 Q. MG90S 9G micro servo https://www.amazon.com/gp/product/B07F7VJQL5
     * x1 S. 250mm 40pin display ribbon cable https://www.amazon.com/gp/product/B00N426GJA  
     * x1 T. mono enclosed speaker - 3W 4 ohm https://www.adafruit.com/product/3351  
     * x1 LL. Servo Tester https://www.amazon.com/gp/product/B07TQSKLBK
     * x1 V. servo horn (packaged with Q MG90S 9G micro servo)
     * x1 W. server screw (packaged with Q MG90S 9G micro servo)
     * x1 MM. PCA9685 16 Channel 12 Bit PWM Servo Driver https://www.amazon.com/gp/product/B07RMTN4NZ
   
### 1. Attach two horizontal braces(A) with 3-hole fastener(B) & attach BNO-055  orientation sensor(E)  

**Parts:**  
   * x2 A. horizontal braces  
   * x1 B. 3-hole fastener  
   * x3 C. 2x8mm round-head self-tapping screws  
   * x4 D. 2x8mm pan-head-with-washer self-tapping screws  
   * x1 E. BNO055 orientation sensor
   

>_**Notes:**_ 
>   * _Make sure Y axis of BNO055(E) points toward picture as shown in image_
>   * _Only fasten one side of the horizontal braces(E)_
     
<img src="./data/images/build-instructions/IMG_3640.jpg" alt="Head Assembly Step 1" width=600 />

---
### 2. Turn 180 degrees and attach camera(F) 

**Parts:**  
   * x1 F. SainSmart IMX219 Camera Module
   * x2 C. 2x8mm round-head self-tapping screws

<img src="./data/images/build-instructions/IMG_3642.jpg" alt="Head Assembly Step 2" width=600 />

---    
### 3. Attach VL53L0X time-of-flight distance sensor(G) 

**Parts:** 
  * x2 H. 1-hole 2mm screw fastener  
  * x2 C. 2x8mm round-head self-tapping screws  
  * x1 G. VL53L0X time-of-flight distance sensor  
<img src="./data/images/build-instructions/IMG_3644.jpg" alt="Head Assembly Step 3" width=600 />
<img src="./data/images/build-instructions/IMG_3645.jpg" alt="Head Assembly Step 3" width=600 />

---     
### 4. Attach camera 15-pin ribbon(I) cable & STEMMA QT cable(J)

**Parts:** 
  * x1 I. 300mm 15-pin camera ribbon cable
  * x1 J. 100mm Stemma QT JST SH 4-pin cable

>_**Notes:**_ 
>   * _Make sure pins of ribbon cable are facing toward contacts and fastened securely_
>   * _Attatch STEMMA QT cable(J) securely to right STEMMA sockets on VL53L0X(G) and BNO055(E)_
   
<img src="./data/images/build-instructions/IMG_3646.jpg" alt="Head Assembly Step 4" width=600 />

---   
### 5. Attach display fasteners(K) and servo adapter(L) to left barrel wall(M)
**Parts:**  
 * x1 M. head barrel wall
 * x1 L. servo adapter
 * x2 K. display fastener
 * x4 D. 2x8mm pan-head-with-washer self-tapping screws

>_**Notes:**_
>   * _Make sure fasteners and raised center lip are on opposite sides_
>   * _Make sure slotted sides of the display fasteners(K) are face up, with open sides pointed inside the circle, and closed ends are pointed out_
>   * _Make sure servo adapter is oriented as shown in image_
>   * _If servo adapter cannot be popped in, soften with a hair dryer or heat gun_
<img src="./data/images/build-instructions/IMG_3647.jpg" alt="Head Assembly Step 5" width=600 />
<img src="./data/images/build-instructions/IMG_3648.jpg" alt="Head Assembly Step 5" width=600 />

---   
### 6. Use the servo tester to set servo to neutral position (90 degrees)
**Parts:**  
   * x1 Q. MG90S 9G micro servo
   * x1 LL. Servo Tester
---   
### 7. Pop servo(Q) into left barrel wall(M)
**Parts:**  
   * x1 Q. MG90S 9G micro servo  
   * x2 M. left barrel wall(M) from step 5  

>_**Notes:**_
>   * _Body of servo should be on same side as fasteners from step 5_  
<img src="./data/images/build-instructions/IMG_3689.jpg" alt="Head Assembly Step 5" width=600 />

---   
### 8. Add shaft(N) to bearing(O)
**Parts:**  
 * x1 N. head shaft adapter 
 * x1 O. bearing 

>_**Notes:**_
>   * _If shaft cannot be popped in, soften with a hair dryer or heat gun_
>   * _The longer side of the shaft should be in the bearing_
<img src="./data/images/build-instructions/IMG_3650.jpg" alt="Head Assembly Step 5" width=600 />

---   
### 9. Attach display fasteners(K) to right barrel wall(M)
**Parts:**  
 * x1 M. head barrel wall
 * x2 K. display fastener

>_**Notes:**_
>  * _Make sure fasteners and raised center lip are on opposite sides_
>  *_Balance weights shown in photo are no-longer used. Please ignore_
<img src="./data/images/build-instructions/IMG_3651.jpg" alt="Head Assembly Step 5" width=600 />

---   
### 10. Pop bearing(O) into right barrel wall(M)
**Parts:**  
 * x1 bearing(O) with shaft(N) from step 8
 * x1 right barrel wall(M) from step 9

>_**Notes:**_
>   * _Make sure shaft is on the opposite side of the clips & weights_
>   * _If bearing cannot be popped in, soften with a hair dryer or heat gun_
<img src="./data/images/build-instructions/IMG_3652.jpg" alt="Head Assembly Step 5" width=600 />


---   
### 11. Attach two horizontal braces(A) with two 3-hole fasteners(B) to create lower head brace
**Parts:**  
   * x2 A. horizontal braces  
   * x2 B. 3-hole fasteners  

>_**Notes:**_
>  * _Make sure to add 3-hole fastener(B) to both sides_
<img src="./data/images/build-instructions/IMG_3653.jpg" alt="Head Assembly Step 5" width=600 />

---   
### 12. Attach bottom head brace to left barrel wall
**Parts:**  
   * x1 Left barrel wall with servo (from step 7)  
   * x1 Lower horizontal head brace (from step 11)  
   * x2 D. 2x8mm pan-head-with-washer self-tapping screws
  
<img src="./data/images/build-instructions/IMG_3654.jpg" alt="Head Assembly Step 5" width=600 />
<img src="./data/images/build-instructions/IMG_3655.jpg" alt="Head Assembly Step 5" width=600 />

---   
### 13. Attach top head brace to left barrel wall
**Parts:**  
   * x1 Left barrel wall with servo (from step 12)  
   * x1 Top horizontal head brace with camera (from step 1)  
   * x2 D. 2x8mm pan-head-with-washer self-tapping screws
  
<img src="./data/images/build-instructions/IMG_3656.jpg" alt="Head Assembly Step 5" width=600 />
<img src="./data/images/build-instructions/IMG_3657.jpg" alt="Head Assembly Step 5" width=600 />

---   
### 14. Attach 40-pin display ribbon(S) to display(R)  
**Parts:**  
   * x1 R. 7in display  
   * x1 S. 250mm 40pin display ribbon cable  

>_**Notes:**_
>   * _Make sure pins of ribbon cable are facing toward contacts and fastened securely_
<img src="./data/images/build-instructions/IMG_3658.jpg" alt="Head Assembly Step 5" width=600 />

---   
### 15. Pop display(S) into clips of left barrel wall(M)
**Parts:**  
   * x1 R. 7in display  
   * x1 left barrel wall with servo (from step 12)  

>_**Notes:**_
>   * _Make sure the cables are on the bottom (opposite camera) and feed bewtween both horizontal braces_

<img src="./data/images/build-instructions/IMG_3690.jpg" alt="Head Assembly Step 5" width=600 />

---   
### 16. Pop right barrel(M) display fasteners(K) onto display and secure to horizontal braces(A) 
**Parts:**  
   * x1 right barrel wall(M) with bearing and shaft (from step 10)
   * x2 D. 2x8mm pan-head-with-washer self-tapping screws

<img src="./data/images/build-instructions/IMG_3659.jpg" alt="Head Assembly Step 5" width=600 />

---   
### 17. Attach speaker(T)
**Parts:**  
   * x1 T. mono enclosed speaker - 3W 4 ohm
   * x2 D. 2x8mm pan-head-with-washer self-tapping screws

<img src="./data/images/build-instructions/IMG_3660.jpg" alt="Head Assembly Step 5" width=600 />

---   
### 18. Pop right L bracket(U) on bearing shaft
**Parts:**  
   * x1 U. head L bracket

>_**Notes:**_
>   * _If shaft does not pop onto L bracket, use hair dryer or heat gun to soften_

<img src="./data/images/build-instructions/IMG_3661.jpg" alt="Head Assembly Step 5" width=600 />

---   
### 19. Attatch servo horn to remaining L bracket(L) and secure with screw(D)
**Parts:**  
   * x1 U. head L bracket
   * x1 V. servo horn
   * x1 D. 2x8mm pan-head-with-washer self-tapping screw

<img src="./data/images/build-instructions/IMG_3662.jpg" alt="Head Assembly Step 5" width=600 />
<img src="./data/images/build-instructions/IMG_3663.jpg" alt="Head Assembly Step 5" width=600 />

---   
### 20. Secure left L bracket to head with servo screw(W)
**Parts:**  
   * x1 W. server screw

>_**Notes:**_
>  * _IMPORTANT: The servo horn should be pointing straight down attached with screen pointing straight left_
>  * _Be careful not to turn servo shaft when attaching. If you do, repeat step 6._

<img src="./data/images/build-instructions/IMG_3665.jpg" alt="Head Assembly Step 5" width=600 />

---   
### 21. The head is now complete and should match the images below:  

<img src="./data/images/build-instructions/IMG_3664.jpg" alt="Head Assembly Step 5" width=600 />
<img src="./data/images/build-instructions/IMG_3665.jpg" alt="Head Assembly Step 5" width=600 />
<img src="./data/images/build-instructions/IMG_3666.jpg" alt="Head Assembly Step 5" width=600 />
<img src="./data/images/build-instructions/IMG_3667.jpg" alt="Head Assembly Step 5" width=600 />

[Return to Table of Contents](#table-of-contents)


---
## Original Project Announcement Videos  
These videos are the original annoucement and project plan for Ro-Bud uploaded to TikTok on 17-April 2021.  

[Return to Table of Contents](#table-of-contents)
### Part 1  
[![Ro-Bud Project - Part 1](https://img.youtube.com/vi/bj4LzYycwYc/0.jpg)](https://www.youtube.com/watch?v=bj4LzYycwYc)  

[Return to Table of Contents](#table-of-contents)
### Part 2
[![Ro-Bud Project - Part 2](https://img.youtube.com/vi/H4fC_qm8pPo/0.jpg)](https://www.youtube.com/watch?v=H4fC_qm8pPo)  

[Return to Table of Contents](#table-of-contents)
### Part 3
[![Ro-Bud Project - Part 3](https://img.youtube.com/vi/r7C16MHGqBg/0.jpg)](https://www.youtube.com/watch?v=r7C16MHGqBg)  

[Return to Table of Contents](#table-of-contents)
### Part 4
[![Ro-Bud Project - Part 4](https://img.youtube.com/vi/n2G9MuK9-XE/0.jpg)](https://www.youtube.com/watch?v=n2G9MuK9-XE)  

[Return to Table of Contents](#table-of-contents)


