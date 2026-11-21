// Customer row details.
var dagcomponentfuncs = window.dashAgGridComponentFunctions =
    window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.DetailsButton = function (props) {
    return React.createElement('button', {
        className: 'detail-button',
        'aria-label': 'View details for ' + props.data.name,
        onClick: function () { props.setData(props.data.id); }
    }, 'View ↗');
};

document.addEventListener('click', function (event) {
    const dialog = document.getElementById('details-dialog');
    if (!dialog || !dialog.open) return;
    if (event.target.closest('#close-details')) dialog.close();
    if (event.target === dialog) {
        const rect = dialog.getBoundingClientRect();
        if (event.clientX < rect.left || event.clientX > rect.right ||
            event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
    }
});
