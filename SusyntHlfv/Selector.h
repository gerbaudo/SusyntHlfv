// emacs -*- C++ -*-
#ifndef HLVF_SELECTOR_H
#define HLVF_SELECTOR_H

#include "SusyntHlfv/ProgressPrinter.h"
#include "SusyntHlfv/CutFlowCounter.h"

#include "SusyNtuple/SusyNtAna.h"
#include "SusyNtuple/SusyDefs.h"
#include "SusyNtuple/EventlistHandler.h"


// fw decl
class DilTrigLogic;
class MCWeighter;

namespace hlfv{

class WeightComponents;
class EventFlags;

class Selector : public SusyNtAna
{
public:
    Selector();
    virtual ~Selector(){};
    virtual void    Begin(TTree *tree);      ///< called before looping on entries
    virtual void    Init(TTree *tree);       ///< called when the TChain is attached
    virtual void    Terminate();             ///< called after looping is finished
    virtual Bool_t  Process(Long64_t entry); ///< called at each event
    ///! whether the current event passes the event criteria (as opposed to object criteria)
    /**
       This function also increments the cutflow counters
     */
    virtual bool passEventCriteria();
    Selector& setEventListFilename(const std::string filename);
    virtual void setDebug(int dbg); ///< overload SusyNtAna::setDebug
protected:
    /// assign the weight components that depend only on event-level variables
    /**
       The output values are assigned to weightcomponents
       \todo using full lumi (LUMI_A_L); need to pass as parameter?
       \todo The input arguments should be const, but their getter
       methods are not declared const, so I cannot do that now.
     */
    static void assignStaticWeightComponents(/*const*/ Susy::SusyNtObject &ntobj,
                                             /*const*/ MCWeighter &weighter,
                                             hlfv::WeightComponents &weightComponents);
    /// compute the event-level flags
    /**
       Note that some of these quantities actually depend on the
       baseline objects, so you need to call it after selectObjects().
     */
    hlfv::EventFlags computeEventFlags();
    /// incremement the event-level counters
    void incrementEventCounters(const hlfv::EventFlags &f, const hlfv::WeightComponents &w);
private:
    /// initialize weighter used for normalization
    bool initMcWeighter(TTree *tree);
    /// convention: we're using an event list if its filename was specified
    bool usingEventList() const { return m_eventListFilename.size()>0; }
    /// initialize event list
    /**
       To be called within Init(), after SusyNtAna::Begin() and after
       initMcWeighter().  Otherwise MCWeighter will get only a subset
       of the events and compute sumw incorrectly.
       Note to self: I am not sure that this feature would work on
       proof. We're not using proof, so who cares.
     */
    bool initEventList(TTree *tree);
protected:
    DilTrigLogic*       m_trigObj;      ///< trigger logic class
    MCWeighter*         m_mcWeighter;   ///< tool to determine the normalization
    hlfv::ProgressPrinter m_printer; ///< tool to print the progress
    hlfv::CutFlowCounter m_counter; ///< counters for cutflow
    std::string m_eventListFilename; ///< name of the file with the eventlist (empty string means don't use this feature)
    bool m_useExistingList;        ///< to keep track of whether there is already an event list
    Susy::EventlistHandler m_eventList; ///< the actual event list
    ClassDef(Selector, 1);
};

} // hlfv

#endif // HLVF_SELECTOR_H
