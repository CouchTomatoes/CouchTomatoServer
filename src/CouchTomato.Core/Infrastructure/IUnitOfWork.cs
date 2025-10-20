namespace CouchTomato.Core.Infrastructure;

public interface IUnitOfWork
{
    Task CommitAsync();
}