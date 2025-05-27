document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    const resumes = document.getElementById('resumes').files;
    const jobDescription = document.getElementById('jobDescription').files[0];
    
    for (let i = 0; i < resumes.length; i++) {
        formData.append('resumes', resumes[i]);
    }
    formData.append('job_description', jobDescription);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        if (response.ok) {
            displayResults(data.results);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while processing the files.');
    }
});

function displayResults(results) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = ''; // Clear previous results
    
    // Create table
    const table = document.createElement('table');
    table.className = 'table table-striped';
    
    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    ['Similarity', 'Name', 'Email', 'Skills', 'Education', 'Experience', 'Resume'].forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Create body
    const tbody = document.createElement('tbody');
    results.forEach(result => {
        const row = document.createElement('tr');
        
        // Similarity (formatted to 2 decimal places)
        const similarityCell = document.createElement('td');
        similarityCell.textContent = (result.Similarity * 100).toFixed(2) + '%';
        row.appendChild(similarityCell);
        
        // Name
        const nameCell = document.createElement('td');
        nameCell.textContent = result.Name;
        row.appendChild(nameCell);
        
        // Email
        const emailCell = document.createElement('td');
        emailCell.textContent = result.Email;
        row.appendChild(emailCell);
        
        // Skills (as comma-separated list)
        const skillsCell = document.createElement('td');
        skillsCell.textContent = Array.isArray(result.Skills) ? result.Skills.join(', ') : result.Skills;
        row.appendChild(skillsCell);
        
        // Education
        const educationCell = document.createElement('td');
        educationCell.textContent = result.Education;
        row.appendChild(educationCell);
        
        // Experience
        const experienceCell = document.createElement('td');
        experienceCell.textContent = result.Experience;
        row.appendChild(experienceCell);
        
        // Resume link
        const resumeCell = document.createElement('td');
        const resumeLink = document.createElement('a');
        resumeLink.href = result.resume_file_link;
        resumeLink.textContent = result.resume_file_name;
        resumeLink.target = '_blank';
        resumeCell.appendChild(resumeLink);
        row.appendChild(resumeCell);
        
        tbody.appendChild(row);
    });
    table.appendChild(tbody);
    resultsDiv.appendChild(table);

    // Add download CSV button
    const downloadButton = document.createElement('button');
    downloadButton.className = 'btn btn-primary mt-3';
    downloadButton.textContent = 'Download CSV';
    downloadButton.onclick = () => downloadCSV(results);
    resultsDiv.appendChild(downloadButton);
}

function downloadCSV(results) {
    // Convert results to CSV
    const headers = ['Similarity', 'Name', 'Email', 'Skills', 'Education', 'Experience', 'Resume File'];
    const csvContent = [
        headers.join(','),
        ...results.map(row => [
            (row.Similarity * 100).toFixed(2) + '%',
            `"${row.Name}"`,
            `"${row.Email}"`,
            `"${Array.isArray(row.Skills) ? row.Skills.join(', ') : row.Skills}"`,
            `"${row.Education}"`,
            `"${row.Experience}"`,
            `"${row.resume_file_name}"`
        ].join(','))
    ].join('\n');

    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'resume_results.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}