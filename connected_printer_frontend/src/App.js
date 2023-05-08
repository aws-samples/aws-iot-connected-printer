// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT.

import './App.css';
import { Button, withAuthenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import React from 'react';



function App({ signOut, user }) {
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
                <span>MBAWS</span>
                <Button onClick={signOut} >Sign out</Button>
            </div>
            <div id="ContentSection">
                <br/>
                <br/>
                <br/>
                <br/>
                <br/>
                <br/>
                <br/>
                <br/>
                <br/>
                <h2>There's nothing here.</h2>
                <p>
                    Use the correct url path to get the content you want.
                </p>
            </div>
        </div>
    );
}

export default withAuthenticator(App);
