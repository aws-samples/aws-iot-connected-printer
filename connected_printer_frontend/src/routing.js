// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT.

import React, {withStore} from 'react';
import App from './App';
import Print from './Print';
import { Route, Routes } from 'react-router-dom';
import { Amplify } from 'aws-amplify';

let initialState = {}





export const Routing = () => {
  return (
    <div>
      <Routes>
        <Route path="/" element={<App/>} />
        <Route path="/print" element={<Print/>} />
      </Routes>
    </div>
  );
};

// export withStore(Routing, intitialState));
