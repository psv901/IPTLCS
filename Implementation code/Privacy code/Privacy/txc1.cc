#include <omnetpp.h>

using namespace omnetpp;

class MyModule : public cSimpleModule {
  private:
    int numInvokes;
    double communicationOverhead;
    simtime_t simulationStartTime;

    cOutVector numInvokesVector;
    cOutVector communicationOverheadVector;
    cOutVector runtimeVector;
    cOutVector tupleLengthVector;

  protected:
    virtual void initialize() override {
        numInvokes = 0;
        communicationOverhead = 0.0;
        simulationStartTime = simTime();

        // Set up output vectors for recording data
        numInvokesVector.setName("Number of Invokes");
        communicationOverheadVector.setName("Communication Overhead");
        runtimeVector.setName("Runtime");
        tupleLengthVector.setName("Tuple Length");
    }

    virtual void handleMessage(cMessage *msg) override {
        // Increment the number of invokes
        numInvokes++;

        //Perform communication overhead measurement
        simtime_t startTime = simTime();
        //communication overhead operations ...
        simtime_t endTime = simTime();
        communicationOverhead += endTime - startTime;

        // Process the message as required

        delete msg;
    }

    virtual void finish() override {
        // Calculate runtime
        simtime_t runtime = simTime() - simulationStartTime;

        // Record data in output vectors
        numInvokesVector.record(numInvokes);
        communicationOverheadVector.record(communicationOverhead.dbl());
        runtimeVector.record(runtime.dbl());
        tupleLengthVector.record(getTupleLength());

    }

    int getTupleLength() {

        return 0;
    }
};

Define_Module(MyModule);

