const fs = require('fs');
let d = fs.readFileSync('static/homework_data.js', 'utf8');
d = d.replace('const HOMEWORK_DATA', 'var HOMEWORK_DATA');
eval(d);
const p = HOMEWORK_DATA.homework1.problems[8];
console.log('Title:', p.title);
console.log('Description:\n', p.description);
console.log('\nTestCases:');
p.testCases.forEach((tc, i) => {
    console.log('--- TC' + (i+1) + ' ---');
    console.log('input:', JSON.stringify(tc.input));
    console.log('expected:', JSON.stringify(tc.expected_output));
});
