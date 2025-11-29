require('module-alias/register');
const moduleAlias = require('module-alias');
const path = require('path');

moduleAlias.addAlias('next/config', path.resolve(__dirname, './next-config-shim.js'));
