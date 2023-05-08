// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT.

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import reportWebVitals from './reportWebVitals';
import { Amplify } from 'aws-amplify';
import { BrowserRouter as Router } from 'react-router-dom';
import { Routing } from './routing';


Amplify.configure({
    Auth: {
        region: 'us-west-2',
        userPoolId: 'us-west-2_XLrgFtfmB',
        userPoolWebClientId: 'ikc8apu3h6c4sf7h5gr22lum8'
    }
})


const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <Router>
    <Routing />
  </Router>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
