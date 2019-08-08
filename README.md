# Master Control Program 


This system is used to secure spaces with an electronic door latch.

## Dependencies:
* [Node + NPM](Node.js)
* [PostgreSQL](http://www.postgresql.org/)
* [Arduino 1.6.5](https://www.arduino.cc/)

## Hardware requirements: 
* [Server protocol RS-485](https://en.wikipedia.org/wiki/RS-485) for the server/client communication.
* [Arduino Nano](https://www.arduino.cc/) for the door client (This is required for the matching footprint).
* [NFC reader](https://www.adafruit.com/products/364). This is the one that we are using for our version of the door lock. 

![Diagram of the door lock project](https://cdn.rawgit.com/MakeICT/electronic-door/v2.0/functional-overview.svg)

* * *

## Todo
* Server
	* Super admins vs group admins
	* Make plugins respect disabled mode
	* When unlocking from web ui, display user in log
	
* Client
	* New NFC reader
	* Add doorbell input (capacitive?)
	* Design/build case for front
	* Build 2nd client for testing & back door

## License 

> Copyright (C) 2014-2016 MakeICT
> 
> This program is free software: you can redistribute it and/or modify it 
> under the terms of the GNU General Public License as published by the 
> Free Software Foundation, either version 3 of the License, or (at your 
> option) any later version.
> 
> This program is distributed in the hope that it will be useful, but 
> WITHOUT ANY WARRANTY; without even the implied warranty of 
> MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU 
> General Public License for more details.
> 
> You should have received a copy of the GNU General Public License along 
> with this program.  If not, see [The GNU licenses page](http://www.gnu.org/licenses)
    
* * *

This is a work in progress. For more information, please visit the [MakeICT Wiki](http://makeict.org/wiki/index.php/Electronic_Door_Entry).

* * *
