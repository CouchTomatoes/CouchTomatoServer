using CouchTomato.Data;

namespace CouchTomato.Core.Infrastructure;

public class UnitOfWork : IUnitOfWork
{
    private readonly CouchTomatoContext _context;

    public UnitOfWork(CouchTomatoContext context)
    {
        _context = context;
    }

    public async Task CommitAsync() => await _context.SaveChangesAsync();
}
