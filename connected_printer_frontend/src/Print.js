// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT.

import './App.css';
import { Button } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import React, { useState, useEffect } from 'react';
import { Amplify } from 'aws-amplify';

const front_end_api_base_uri = "https://578o5hgm0g.execute-api.us-west-2.amazonaws.com/prod"
const printers_uri = front_end_api_base_uri+"/printers" 
const availability_uri = front_end_api_base_uri+"/availability"
const print_uri = front_end_api_base_uri+"/print"
const print_status_uri = front_end_api_base_uri+"/print_status"

const card_graphics = [
    {
        'card_id': 'anybank-sworl-n.png',
        'card_id_un': 'anybank-sworl-un.png',
        'location': '/img/anybank-sworl-n.png',
        'location_un': '/img/anybank-sworl-un.png'
    },
    {
        'card_id': 'anybank-pink-1-n.png',
        'card_id_un': 'anybank-pink-1-un.png',
        'location': '/img/anybank-pink-1-n.png',
        'location_un': '/img/anybank-pink-1-un.png'
    },
    {
        'card_id': 'anybank-pink-2-n.png',
        'card_id_un': 'anybank-pink-2-un.png',
        'location': '/img/anybank-pink-2-n.png',
        'location_un': '/img/anybank-pink-2-un.png'
    }
]

function DisplayDevices({device, setModal, setModalContent, selectedCustomer, selectedLocation, authData, setAuthData}) {
    const [deviceAvailability, setDeviceAvailability] = useState("")
    const [deviceExpanded, setDeviceExpanded] = useState(false)

    /*eslint-disable */


    useEffect(() => {
        const fetchData = async (device_id) => {
            try {
                const response = await fetch(availability_uri, {
                    method: 'POST',
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${authData}`
                    },
                    body: JSON.stringify({device_id: device_id})
                });
                const json = await response.json();
                let d = new Date(json.body.last_seen*1000)
                json.body.readable_dt = d.toString()
                console.log(json.body)
                setDeviceAvailability(json.body)
            } catch (error) {
                console.log("error", error);
                setDeviceAvailability({ 'readable_dt': 'More than 30 minutes ago' })
            }
        };
        fetchData(device.device_id);
    }, [])
    /*eslint-enable */

    function getDeviceAvailability(device_id) {
        console.log('calling device_avail api')
        console.log('device_id is: '+device_id)

        const fetchData = async () => {
            try {
                const response = await fetch(availability_uri, {
                    method: 'POST',
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${authData}`
                    },
                    body: JSON.stringify({device_id: device_id})
                });
                const json = await response.json();
                // console.log(json);
                let d = new Date(json['body'].last_seen*1000)
                // console.log(d)
                json['body'].readable_dt = d.toString()
                console.log(json['body'])
                setDeviceAvailability(json['body'])
            } catch (error) {
                console.log("error", error);
                setDeviceAvailability({ 'readable_dt': 'More than 30 minutes ago' })
            }
        };

        fetchData();
    }

    function createJob(device, selectedCustomer, selectedLocation) {
        console.log('Creating job for: '+ device.device_id)
        setModalContent({
            'device_name': device.device_name,
            'device_id': device.device_id,
            'customer': selectedCustomer,
            'location': selectedLocation
        })
        setModal(1)
    }

    return (
        <div key={device.device_id} id="deviceContainer">
            <div className="device" 
                value={device.device_id} 
                // onClick={() => handleDeviceSelection}
                style={{
                    height: deviceExpanded ? '240px': '50px'
                }}>
                <div className="deviceNav" id="DeviceNav">
                    <div className="deviceLabel">
                        <svg viewBox="0 0 32 32">
                            <path d="M26 23h-2v-2h1v-2h-19v2h1v2h-2c-0.552 0-1-0.448-1-1v-10c0-0.967 4-2 11-2 0.371 0 0.699 0 1 0 6.938 0 11 1.010 11 2v10c0 0.552-0.447 1-1 1zM23.5 13c-0.828 0-1.5 0.672-1.5 1.5s0.672 1.5 1.5 1.5 1.5-0.672 1.5-1.5-0.672-1.5-1.5-1.5zM8 4c0-0.553 0.448-1 1-1h13c0.553 0 1 0.447 1 1v5h-15v-5zM23 29c0 0.552-0.447 1-1 1h-13c-0.552 0-1-0.448-1-1v-9h15v9zM21 21h-11v1h11v-1zM21 23h-11v1h11v-1zM21 25h-11v1h11v-1zM21 27h-11v1h11v-1z"></path>
                        </svg> 
                        <span><b>{device.device_name}</b></span>
                    </div>
                    <div className="deviceStatus">
                        <span>Status: &nbsp;<b style={{
                            color: deviceAvailability.is_available !== true ? '#912a1e': '#1d5521'
                        }}>{deviceAvailability.is_available !== true ? 'Offline': 'Ready'}</b></span>
                        { deviceExpanded === false &&
                            <div className="DeviceExpandButton">
                                <svg viewBox="0 0 32 32" onClick={() => setDeviceExpanded(!deviceExpanded)}>
                                    <path d="M24 18h-6v6h-4v-6h-6v-4h6v-6h4v6h6v4z"></path>
                                </svg>
                            </div>
                        }
                        { deviceExpanded === true &&
                            <div className="DeviceExpandButton">
                                <svg viewBox="0 0 32 32" onClick={() => setDeviceExpanded(!deviceExpanded)}>
                                    <path d="M24 14v4h-16v-4h16z"></path>
                                </svg>
                            </div>
                        }
                    </div>
                </div>
                <div className="deviceDetails">
                    <span className="deviceDetail">
                        <span><b>Last Seen:</b></span>
                        <span>
                            { deviceAvailability.readable_dt }
                        </span>
                        </span>
                        <div className="deviceActionsContainer">
                        <Button onClick={() => getDeviceAvailability(device.device_id)}>Refresh Status</Button>
                        <Button variation="primary" disabled={deviceAvailability.is_available !== true ? true: false} onClick={() => createJob(device, selectedCustomer, selectedLocation)}>Create Job</Button>
                        </div>
                </div>
            </div>
        </div>
    )
}

function Print({ signOut, user }) {
    const [modal, setModal] = useState(0);
    const [modalContent, setModalContent] = useState({
        'printer_name': 'unset',
        'printer_id': 'unset',
        'customer': 'unset',
        'location': 'unset'
    });
    const [printers, setPrinters] = useState([])
    const [selectedCustomer, setSelectedCustomer] = useState("")
    const [customerLocations, setCustomerLocations] = useState([])
    const [selectedLocation, setSelectedLocation] = useState("None")
    const [locationDevices, setLocationDevices] = useState([])
    const [firstName, setFirstName] = useState("")
    const [lastName, setLastName] = useState("")
    const [printJobStatus, setPrintJobStatus] = useState(null)
    const [selectedCard, setSelectedCard] = useState(null)
    const [printReady, setPrintReady] = useState(false)
    const [printJobSent, setPrintJobSent] = useState(false)
    /*eslint-disable */
    const [printJobID, setPrintJobID] = useState(null)
    const [loop, setLoop] = useState(null)
    /*eslint-enable */
    const [jobModal, setJobModal] = useState(0)
    const [authData, setAuthData] = useState({})


    useEffect(() => {

        const fetchData = async () => {
            try {
                const getAuth = await Amplify.Auth.currentSession()
                console.log(getAuth.idToken.jwtToken)
                setAuthData(getAuth.idToken.jwtToken)
                const response = await fetch(printers_uri, {
                    method: 'GET',
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${getAuth.idToken.jwtToken}`
                    }
                });
                const json = await response.json();
                console.log(json.body);
                setPrinters(JSON.parse(json.body))
            } catch (error) {
                console.log("error", error)
            }

        };
        fetchData();
    }, [])

    const stopStatusInterval = () => {
        setLoop(interval => {
            clearInterval(interval);
            return null;
        })
    }

    function handleCustomerSelection(e) {
        if(e.target.value === "None" ) {
            setSelectedCustomer("None")
            setSelectedLocation("None")
            setLocationDevices([])
        } else {
            e.preventDefault()
            setSelectedCustomer(e.target.value)
            setLocationDevices([])
            setSelectedLocation("None")
            // console.log(printers)
            let cxLocations = printers[printers
                .map(({ customer }) => customer)
                .indexOf(e.target.value)]
                .locations.map(({ location }) => location)
            // console.log(cxLocations)
            setCustomerLocations(cxLocations)
        }
    }

    function handleLocationSelection(e) {
        e.preventDefault()
        if(e.target.value === "None" ) {
            setSelectedLocation("None")
            setLocationDevices([])
        } else {
            setSelectedLocation(e.target.value)
            let cxPrinters = printers[printers.map(({ customer }) => customer).indexOf(selectedCustomer)]
                .locations.map(({ devices_at_location }) => devices_at_location)
            console.log(cxPrinters[0])
            setLocationDevices(cxPrinters[0])
        }
        
    }

    /*eslint-disable */
    function uuidv4() { 
        // eslint-disable-next-line no-use-before-define
        return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c => 
          (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16) 
        ); 
    } 
    /*eslint-enable */

    function callPrintJobStatusAPI(payload) {
        console.log('calling print job status api')

        const fetchData = async () => {
            // let id_token = getAuth();
            try {
                const response = await fetch(print_status_uri, {
                    method: 'POST',
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${authData}`
                    },
                    body: JSON.stringify(payload)
                });
                const json = await response.json();
                let json_body = JSON.parse(json['body'])
                console.log(json_body)
                console.log(json_body.job_status)
                
                if(json_body.job_status === "Succeeded" || json_body.job_status=== "Failed"  ) {
                    console.log('print job status wasnt succeeded or failed')
                    setPrintJobStatus(json_body)

                    stopStatusInterval()
                } else {
                    console.log("hmmm")
                }
            } catch (error) {
                console.log("error", error);
            }
        };

        fetchData();
    }

    function callPrintJobAPI(payload) {
        console.log('calling print job api')
        console.log('payload is: ')
        console.log(payload)
        setJobModal(!jobModal)
        const fetchData = async () => {
            try {
                const response = await fetch(print_uri, {
                    method: 'POST',
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${authData}`
                    },
                    body: JSON.stringify(payload)
                });
                const json = await response.json();
                console.log(json['body'])
                
                setLoop(
                    setInterval(() => {
                        callPrintJobStatusAPI(payload)
                    }, 1000)
                );
            } catch (error) {
                console.log("error", error);
            }
        };
        fetchData();
    }


    function submitPrintJob() {
        console.log('submitting print job')
        let payload = modalContent
        payload.firstName = firstName
        payload.lastName = lastName
        payload.job_id = uuidv4().toString()
        setPrintJobID(payload.job_id)
        payload.card_design = selectedCard.card_id_un
        setPrintJobSent(true)
        determinePrintReady('print', true)
        callPrintJobAPI(payload)
    }

    function determinePrintReady(type, value) {
        switch(type) {
            case "print":
                if (value === false) {
                    console.log('print is ready')
                    setPrintReady(true)
                } else {
                    console.log('print is not ready')
                    setPrintReady(false)
                }
                break;
            case "firstName":
                if (value.length >=2 && lastName.length >=2 && selectedCard !== null && printJobSent === false) {
                    console.log('print is ready')
                    setPrintReady(true)
                } else {
                    console.log('print is not ready')
                    setPrintReady(false)
                }
                break;
            case "lastName":
                if (value.length >=2 && firstName.length >=2 && selectedCard !== null && printJobSent === false) {
                    console.log('print is ready')
                    setPrintReady(true)
                } else {
                    console.log('print is not ready')
                    setPrintReady(false)
                }
                break;
            case "card":
                if (lastName.length >= 2 && lastName.length >=2 && printJobSent === false) {
                    console.log('print is ready')
                    setPrintReady(true)
                } else {
                    console.log('print is not ready')
                    setPrintReady(false)
                }
                break;
            default:
                break;
        }
        
    }

    function handleSelectedCard(card) {
        // e.preventDefault()
        setSelectedCard(card)
        determinePrintReady('card', card)
    }

    function handleFirstNameChange(e) {
        e.preventDefault()
        setFirstName(e.target.value)
        determinePrintReady('firstName', e.target.value)
    }

    function handleLastNameChange(e) {
        e.preventDefault()
        setLastName(e.target.value)
        determinePrintReady('lastName', e.target.value)
    }

    function logInformation() {
        console.log('Selected Customer: '+selectedCustomer)
        console.log('Available Locations: '+customerLocations)
        console.log('Selected Location: '+selectedLocation)
        console.log('Selected Device Name: '+locationDevices[0].device_name)
        console.log('Selected Device ID: '+locationDevices[0].device_id)
    }

    function handleJobModalContinue() {
        setFirstName("")
        setLastName("")
        setSelectedCustomer("None")
        setSelectedLocation("None")
        setSelectedCard(null)
        setLocationDevices([])
        setPrintJobSent(false)
        setPrintReady(false)
        setJobModal(!jobModal)
        setModal(!modal)
        setPrintJobStatus(null)
    }

    return (
        <div className="App">
             <div className="airwolf-header">
                <span className="airwolf-header-stripe-shine one"></span>
                <span className="airwolf-header-stripe-shine two"></span>
                <span className="airwolf-header-stripe-fade one"></span>
                <span className="airwolf-header-stripe-fade two"></span>
                <span className="airwolf-header-stripe-fade three"></span>
                <span className="airwolf-header-stripe-fade four"></span>
                <span className="airwolf-header-stripe-fade five"></span>
            </div>
            <div id="UpperNav">
                <span>AWS IoT Connected Printer</span>
                <Button onClick={signOut} >Sign out</Button>
            </div>
            <div id="ContentSection">
                <h2>Create a Print Job</h2>
                <div className="FormSection">
                    <form>
                        <h3>Customer Information</h3>
                        <span>
                            <label>Customer:</label>
                            <select id='customer' name='customer' onChange={handleCustomerSelection} value={selectedCustomer}>
                                <option value="None">Please Select an Option</option>
                                {
                                    printers.map(printer => (
                                        <option key={printer.customer} value={printer.customer}>{printer.customer}</option>
                                    ))
                                }
                            </select>
                        </span>
                        <span>
                            <label>Location:</label>
                            <select id='location' name='location' onChange={handleLocationSelection} value={selectedLocation}>
                                <option value="None">Please Select an Option</option>
                                {
                                    customerLocations.map(location => (
                                        <option key={location} value={location}>{location}</option>
                                    ))
                                }
                            </select>
                        </span>
                        <span id="devicesContainer">
                            { selectedLocation !== "None" &&
                                <label>Devices:</label> 
                            }
                            {
                                locationDevices.map(device => (
                                    <DisplayDevices device={device} 
                                                    key={device.device_id}
                                                    setModal={setModal} 
                                                    setModalContent={setModalContent} 
                                                    selectedCustomer={selectedCustomer}
                                                    selectedLocation={selectedLocation}
                                                    authData={authData}
                                                    setAuthData={setAuthData}
                                    />
                                ))
                            }
                        </span>
                    </form>
                    <button onClick={() => logInformation()} className="LogButton">Log Stuff</button>
                </div>
                <div id="Modal" style={{ 
                    maxHeight: modal ? '80vh' : '0px',
                    opacity: modal ? '1':'0',
                    border: modal ? '1px solid black':'none'
                    }}>
                    <div id="ModalUpperNav">
                        <h4>Create Print Job</h4>
                        <Button onClick={() => setModal(0)}>Close</Button>
                    </div>
                    <div className="ModalForm">
                        <h4>Customer Information</h4>
                        <span className="CustInfoSpan"><span id="cis1">Customer:</span> <span>{modalContent.customer}</span></span>
                        <span className="CustInfoSpan"><span id="cis1">Location:</span> <span>{modalContent.location}</span></span>
                        <span className="CustInfoSpan"><span id="cis1">Device:</span> <span>{modalContent.device_name}</span></span>
                        
                        <br/>
                        <h4>Cardholder Information</h4>
                        <div className="CardholderInfo">
                            <span>
                                <label>First Name:</label>
                                <input type="text" onChange={handleFirstNameChange} value={firstName} />  
                            </span>
                            <span>
                                <label>Last Name:</label>
                                <input type="text" onChange={handleLastNameChange} value={lastName} />  
                            </span>
                        </div>
                    </div>
                    <div className="CardSelectionContainer" >
                        <h4>Select Card Design</h4>
                        <div className="CardOptions">
                        {
                            card_graphics.map(card => (
                                <img className="CardGraphic" alt={`small version of a design to be selected: ${card.card_id}`} key={card.card_id} src={card.location} onClick={() => handleSelectedCard(card)} />
                            ))
                        }
                        </div>
                        <div className="SelectedCardContainer">
                            {
                                selectedCard !== null &&
                                <img className="SelectedCardGraphic" src={selectedCard.location_un}  alt={`large version of a design that is selected: ${selectedCard.card_id}`} />
                            }
                            {  
                                (firstName.length >= 2 && lastName.length >= 2  && selectedCard !== null) &&
                                <span className="CardName">{firstName}&nbsp;{lastName}</span>
                            
                            }
                        </div>
                    </div>
                    <div className="ModalButtons">
                        <Button  variation="primary"  disabled={!printReady} className="SubmitButton" onClick={() => submitPrintJob()}>
                            { printJobSent ? "Printing...": "Submit" }
                        </Button>
                    </div>

                    <div id="JobModalContainer" style={{
                        display: jobModal ? 'flex': 'none'
                    }}>
                        <div id="JobModal" style={{
                            maxHeight: jobModal ? '40vh' : '0px',
                            opacity: jobModal ? '1':'0',
                            border: jobModal ? '1px solid black':'none'
                        }}>
                            <div id="ModalUpperNav" className="JobModalNav">
                            </div>
                            { printJobStatus === null &&
                                <span className="JobModalContent">
                                    <p>Your card is currently printing. Please wait.</p>
                                    <div className="lds-spinner"><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div></div>
                                </span>                               
                            }
                            { printJobStatus !== null &&
                                <span className="JobModalContent">
                                    <p>Your card has successfully printed.</p>
                                    <Button onClick={() => handleJobModalContinue()}>Go Back</Button>
                                </span>  

                            }
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Print;
