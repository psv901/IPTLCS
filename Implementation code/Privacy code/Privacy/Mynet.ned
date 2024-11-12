//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
// 
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
// 
import org.car2x.veins.nodes.RSU;
import org.car2x.veins.nodes.Scenario;
import IVSP;
import Vehicle;

//
// TODO auto-generated type
//
network Mynet
{
    @display("bgb=600,400");
    
    submodules:
        rsu: RSU {
            @display("p=150,140;i=veins/sign/yellowdiamond;is=vs");
        }
        rsu1: RSU {
            @display("p=80,40;i=veins/sign/yellowdiamond;is=vs");
        }
        ivsp: IVSP {
            @display("p=260,140;i=veins/sign/yellowdiamond;is=vs");
        }
        vehicle: Vehicle {
            @display("p=200,250;i=veins/sign/car;pixmap=car1,64");
        }
        
    connections allowunconnected:
        vehicle.mobilityOut --> rsu.mobilityIn;
        vehicle.mobilityIn <-- rsu.mobilityOut;
        rsu.mobilityOut --> ivsp.mobilityIn;
        rsu.mobilityIn <-- ivsp.mobilityOut;
        
        rsu.mobilityOut --> rsu1.mobilityIn;
        rsu.mobilityIn <-- rsu1.mobilityOut;


//        vehicle[0].mobilityOut --> rsu.mobilityIn;
//        vehicle[0].mobilityIn <-- rsu.mobilityOut;
//        rsu.mobilityOut --> ivsp.mobilityIn;
//        rsu.mobilityIn[0] <-- ivsp.mobilityOut;
//        
//        rsu.mobilityOut --> rsu1.mobilityIn[0];
//        rsu.mobilityIn[0] <-- rsu1.mobilityOut;
        
//        vehicle[1].mobilityIn --> ivsp[1].mobilityIn;
//        vehicle[1].mobilityOut <-- ivsp[1].mobilityOut;
}
